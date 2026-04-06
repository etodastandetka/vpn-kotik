import hashlib
import hmac
import json
from typing import Any

import httpx

from app.config import settings


def crypto_pay_base_url() -> str:
    if settings.crypto_pay_use_testnet:
        return "https://testnet-pay.crypt.bot"
    return "https://pay.crypt.bot"


def verify_webhook_signature(api_token: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not api_token:
        return False
    secret = hashlib.sha256(api_token.encode()).digest()
    check = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(check, signature_header)


async def create_invoice(
    *,
    amount: str,
    asset: str,
    description: str,
    payload: str,
    paid_btn_url: str | None = None,
    expires_in: int | None = 300,
) -> dict[str, Any]:
    token = settings.crypto_pay_token
    if not token:
        raise ValueError("CRYPTO_PAY_TOKEN is not set")

    url = f"{crypto_pay_base_url()}/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": token}
    body: dict[str, Any] = {
        "asset": asset,
        "amount": amount,
        "description": description[:1024],
        "payload": payload[:4096],
        "allow_comments": False,
    }
    if expires_in is not None:
        body["expires_in"] = expires_in
    if paid_btn_url:
        body["paid_btn_url"] = paid_btn_url[:1024]

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", data))
    return data["result"]


def parse_invoice_payload(webhook_json: dict[str, Any]) -> tuple[int, str] | None:
    """
    Expects Crypto Pay webhook JSON. Returns (telegram_id, plan_id) or None.
    """
    if webhook_json.get("update_type") != "invoice_paid":
        return None
    payload_obj = webhook_json.get("payload")
    if not isinstance(payload_obj, dict):
        return None
    raw = payload_obj.get("payload")
    if not isinstance(raw, str) or "|" not in raw:
        return None
    left, right = raw.split("|", 1)
    try:
        tid = int(left.strip())
    except ValueError:
        return None
    plan_id = right.strip()
    if not plan_id:
        return None
    return tid, plan_id


def parse_webhook_body(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))
