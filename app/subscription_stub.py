"""Формирование config_stub для подписки (URL панели или многострочные ссылки)."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_DEFAULT_PLACEHOLDER_HOST = "vpn.example.com"


def build_config_stub(
    template: str | None,
    *,
    telegram_id: int,
    plan_id: str,
    user_id: int,
) -> str:
    """
    Если template задан и не пустой — подставляет {telegram_id}, {plan_id}, {user_id}.
    Иначе — явная заглушка (для разработки; в проде задайте SUBSCRIPTION_STUB_TEMPLATE).
    """
    raw = (template or "").strip()
    if raw:
        try:
            return raw.format(telegram_id=telegram_id, plan_id=plan_id, user_id=user_id)
        except KeyError as e:
            log.warning("SUBSCRIPTION_STUB_TEMPLATE: неизвестный плейсхолдер %s", e)
            return raw
    log.warning(
        "SUBSCRIPTION_STUB_TEMPLATE не задан — используется заглушка %s. "
        "Укажите URL подписки из 3x-ui в .env до продакшена.",
        _DEFAULT_PLACEHOLDER_HOST,
    )
    return f"https://{_DEFAULT_PLACEHOLDER_HOST}/config/{telegram_id}?plan={plan_id}"
