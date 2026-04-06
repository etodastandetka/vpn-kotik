"""Публичная ссылка подписки /sub/{token} для клиентов (Happ, v2rayNG и т.д.)."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.models import User

log = logging.getLogger(__name__)


async def ensure_public_sub_token(session: AsyncSession, user: User) -> str:
    if user.public_sub_token:
        return user.public_sub_token
    import secrets

    for _ in range(10):
        token = secrets.token_hex(16)
        existing = await session.scalar(select(User.id).where(User.public_sub_token == token))
        if existing is None:
            user.public_sub_token = token
            await session.flush()
            return token
    msg = "Не удалось выделить токен подписки"
    raise RuntimeError(msg)


async def get_user_by_public_token(session: AsyncSession, token: str) -> User | None:
    if not token or len(token) > 64:
        return None
    return await session.scalar(select(User).where(User.public_sub_token == token))


async def build_subscription_body(config_stub: str) -> tuple[bytes, str]:
    """
    Тело ответа для URL подписки.

    - Если в БД лежит https-URL панели (готовая subscription link) — проксируем ответ как есть.
    - Если лежат строки vless/vmess/trojan — отдаём в формате, принятом в v2ray:
      тело = base64 от UTF-8 текста (строки ссылок через \\n).
    """
    stub = (config_stub or "").strip()
    if not stub:
        return b"", "text/plain; charset=utf-8"

    if stub.startswith("http://") or stub.startswith("https://"):
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            try:
                r = await client.get(
                    stub,
                    headers={
                        "User-Agent": "Happ/3.0 (Windows) (subscription)",
                        "Accept": "*/*",
                    },
                )
                r.raise_for_status()
            except httpx.HTTPError:
                log.exception("subscription proxy fetch failed")
                raise
            return r.content, "text/plain; charset=utf-8"

    lines = [ln.strip() for ln in stub.splitlines() if ln.strip()]
    if not lines:
        return b"", "text/plain; charset=utf-8"
    joined = "\n".join(lines)
    b64 = base64.b64encode(joined.encode("utf-8")).decode("ascii")
    return b64.encode("utf-8"), "text/plain; charset=utf-8"


def subscription_import_url(token: str) -> str:
    """Полный URL, который вставляют в Happ как «URL подписки»."""
    from app.config import settings

    base = (settings.public_api_base_url or settings.webhook_base_url or "").strip().rstrip("/")
    return f"{base}/sub/{token}"
