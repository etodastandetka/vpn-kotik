from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень репозитория (рядом с папкой app) — чтобы .env находился при запуске из bot/ или из корня
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://vpn:vpn@localhost:5432/vpn"
    bot_token: str = ""
    crypto_pay_token: str = ""
    crypto_pay_use_testnet: bool = False
    webhook_base_url: str = "http://localhost:8000"
    # База для ссылки подписки Happ (https://ваш-домен). Пусто = берётся webhook_base_url
    public_api_base_url: str = ""
    crypto_webhook_path: str = "/webhooks/crypto-pay"

    cardlink_token: str = ""
    cardlink_shop_id: str = ""
    cardlink_base_url: str = "https://cardlink.link"
    cardlink_webhook_path: str = "/webhooks/cardlink"

    referral_bonus_days: int = 7

    support_username: str = ""
    support_info_url: str = ""

    # URL подписки 3x-ui или шаблон с плейсхолдерами {telegram_id}, {plan_id}, {user_id}.
    # Пусто = заглушка в логах (см. app/subscription_stub.py).
    subscription_stub_template: str = ""

    # Веб-админка (Next.js) ходит в FastAPI с заголовком X-Admin-Key
    admin_api_key: str = ""
    prometheus_base_url: str = ""
    prometheus_timeout_sec: float = 10.0
    # JSON: [{"id":"nl1","name":"Node 1","instance":"1.2.3.4:9100","panel_health_url":"https://..."}]
    monitor_nodes_json: str = "[]"
    monitor_cpu_warn_pct: float = 85.0
    monitor_mem_warn_pct: float = 90.0
    monitor_disk_warn_pct: float = 90.0
    monitor_panel_timeout_sec: float = 8.0


settings = Settings()
