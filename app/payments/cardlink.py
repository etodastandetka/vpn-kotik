"""
Cardlink (cardlink.link): POST /api/v1/bill/create и postback оплаты.
Документация: https://cardlink.link/reference/api

Создание счёта — как в примерах curl: application/x-www-form-urlencoded.
Postback на Result URL — application/x-www-form-urlencoded, подпись:
  SignatureValue = strtoupper(md5(OutSum + ":" + InvId + ":" + apiToken))
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import Any

import httpx

from app.config import settings


def cardlink_api_base() -> str:
    base = settings.cardlink_base_url.rstrip("/")
    if not base.endswith("/api/v1"):
        base = f"{base}/api/v1"
    return base + "/"


def _form_truthy_success(val: Any) -> bool:
    if val is True or val == 1:
        return True
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return False


def verify_payment_postback_signature(out_sum: str, inv_id: str, signature_value: str, api_token: str) -> bool:
    """strtoupper(md5(OutSum . ':' . InvId . ':' . apiToken))"""
    if not api_token or not signature_value:
        return False
    raw = f"{out_sum}:{inv_id}:{api_token}"
    expected = hashlib.md5(raw.encode("utf-8")).hexdigest().upper()
    got = signature_value.strip().upper()
    return hmac.compare_digest(expected, got)


def form_get_ci(form_dict: dict[str, Any], *candidates: str) -> str | None:
    """Поиск поля без учёта регистра ключей (Cardlink шлёт PascalCase)."""
    lower_map = {str(k).lower(): v for k, v in form_dict.items()}
    for name in candidates:
        key = name.lower()
        if key in lower_map:
            v = lower_map[key]
            if v is None:
                return None
            return str(v)
    return None


async def create_bill(
    *,
    amount_rub: float,
    shop_id: str,
    order_id: str,
    custom_payload: str,
    description: str,
    name: str,
    currency_in: str = "RUB",
    bill_type: str = "normal",
    payer_pays_commission: bool = False,
) -> dict[str, Any]:
    token = settings.cardlink_token
    if not token:
        raise ValueError("CARDLINK_TOKEN is not set")
    if not shop_id:
        raise ValueError("CARDLINK_SHOP_ID is not set")

    url = cardlink_api_base() + "bill/create"
    headers = {"Authorization": f"Bearer {token}"}
    # Как в официальных curl: -d key=value (form-urlencoded)
    data: dict[str, str] = {
        "amount": str(amount_rub),
        "shop_id": shop_id,
        "order_id": order_id,
        "description": description[:1024],
        "name": name[:255],
        "custom": custom_payload[:4096],
        "payer_pays_commission": "1" if payer_pays_commission else "0",
        "type": bill_type,
        "currency_in": currency_in,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, data=data)
        try:
            resp: dict[str, Any] = r.json()
        except Exception as exc:
            raise RuntimeError(f"Cardlink HTTP {r.status_code}: {r.text[:500]}") from exc

    if not _form_truthy_success(resp.get("success")):
        msg = resp.get("message") or resp.get("errors") or resp
        raise RuntimeError(str(msg))

    return resp


def extract_success_payment_fields(form_dict: dict[str, Any]) -> dict[str, Any] | None:
    """
    Поля postback при успешной оплате (Status уже проверен вызывающим кодом).
    Документация: InvId, OutSum, TrsId, CurrencyIn, custom.
    """
    custom = form_get_ci(form_dict, "custom", "Custom")
    if not custom or "|" not in custom:
        return None

    left, right = custom.split("|", 1)
    try:
        telegram_id = int(left.strip())
    except ValueError:
        return None
    plan_id = right.strip()
    if not plan_id:
        return None

    trs_id = form_get_ci(form_dict, "TrsId", "trs_id")
    if not trs_id:
        return None

    out_sum = form_get_ci(form_dict, "OutSum", "out_sum") or ""
    inv_id = form_get_ci(form_dict, "InvId", "inv_id") or ""
    currency = form_get_ci(form_dict, "CurrencyIn", "currency_in") or "RUB"
    return {
        "telegram_id": telegram_id,
        "plan_id": plan_id,
        "trs_id": trs_id,
        "inv_id": inv_id,
        "out_sum": out_sum,
        "currency": currency,
        "raw_custom": custom,
    }


def parse_payment_postback_form(form_dict: dict[str, Any]) -> dict[str, Any] | None:
    """Обёртка: только SUCCESS + валидный custom."""
    status = form_get_ci(form_dict, "Status", "status")
    if not status or str(status).upper() != "SUCCESS":
        return None
    return extract_success_payment_fields(form_dict)


def new_order_id() -> str:
    return str(uuid.uuid4())
