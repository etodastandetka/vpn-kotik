from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

from app.config import settings
from app.database import async_session_maker
from app.services.subscription import get_active_subscription
from app.services.subscription_link import build_subscription_body, get_user_by_public_token
from app.payments.cardlink import (
    extract_success_payment_fields,
    form_get_ci,
    verify_payment_postback_signature,
)
from app.payments.crypto_pay import parse_invoice_payload, parse_webhook_body, verify_webhook_signature
from app.services.subscription import apply_paid_plan, delete_pending_cardlink_by_bill
from app.admin_routes import router as admin_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="VPN Subscription API", lifespan=lifespan)
app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/sub/{token}")
async def subscription_feed(token: str):
    """
    URL подписки для Happ / v2ray-клиентов: отдаёт text/plain (часто base64 со списком ссылок).
    В браузере страницы как у сторонних сервисов нет — только «сырой» фид; шрифты .woff2 на сайтах к конфигу не относятся.
    """
    async with async_session_maker() as session:
        user = await get_user_by_public_token(session, token)
        if not user:
            raise HTTPException(status_code=404, detail="Unknown token")
        sub = await get_active_subscription(session, user.id)
        stub = (sub.config_stub if sub else None) or ""
        if not sub or not stub.strip():
            raise HTTPException(status_code=404, detail="No active subscription or empty config")
        try:
            body, media_type = await build_subscription_body(stub)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail="Failed to fetch upstream subscription") from e
        if not body:
            raise HTTPException(status_code=404, detail="Empty body")
        return Response(
            content=body,
            media_type=media_type,
            headers={"Cache-Control": "no-store"},
        )


@app.post(settings.crypto_webhook_path)
async def crypto_pay_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Crypto-Pay-Api-Signature")
    if not verify_webhook_signature(settings.crypto_pay_token, body, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = parse_webhook_body(body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON") from None

    parsed = parse_invoice_payload(data)
    if not parsed:
        return {"ok": True}

    telegram_id, plan_id = parsed
    inv = data.get("payload")
    if not isinstance(inv, dict):
        return {"ok": True}

    invoice_id = inv.get("invoice_id")
    external_id = str(invoice_id) if invoice_id is not None else None
    amount = str(inv["amount"]) if inv.get("amount") is not None else None
    currency = str(inv["asset"]) if inv.get("asset") is not None else None
    raw_payload = inv.get("payload")
    payload_str = str(raw_payload) if raw_payload is not None else None

    async with async_session_maker() as session:
        await apply_paid_plan(
            session,
            telegram_id=telegram_id,
            plan_id=plan_id,
            provider="crypto",
            external_id=external_id,
            amount=amount,
            currency=currency,
            payload=payload_str,
        )

    return {"ok": True}


@app.post(settings.cardlink_webhook_path)
async def cardlink_payment_webhook(request: Request):
    """
    Result URL в настройках магазина Cardlink. Формат: application/x-www-form-urlencoded.
    Подпись: strtoupper(md5(OutSum + ':' + InvId + ':' + apiToken)).
    """
    if not settings.cardlink_token:
        raise HTTPException(status_code=503, detail="CARDLINK_TOKEN is not set")

    form = await request.form()
    form_dict = dict(form)

    out_sum = form_get_ci(form_dict, "OutSum", "out_sum") or ""
    inv_id = form_get_ci(form_dict, "InvId", "inv_id") or ""
    sig = form_get_ci(form_dict, "SignatureValue", "signature_value") or ""

    if not verify_payment_postback_signature(out_sum, inv_id, sig, settings.cardlink_token):
        raise HTTPException(status_code=403, detail="Invalid Cardlink signature")

    status = form_get_ci(form_dict, "Status", "status")
    if str(status or "").upper() != "SUCCESS":
        return {"ok": True}

    parsed = extract_success_payment_fields(form_dict)
    if not parsed:
        return {"ok": True}

    async with async_session_maker() as session:
        await delete_pending_cardlink_by_bill(session, parsed["trs_id"])
        await apply_paid_plan(
            session,
            telegram_id=parsed["telegram_id"],
            plan_id=parsed["plan_id"],
            provider="cardlink",
            external_id=parsed["trs_id"],
            amount=parsed["out_sum"],
            currency=parsed["currency"],
            payload=parsed["raw_custom"],
        )

    return {"ok": True}
