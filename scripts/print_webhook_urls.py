"""Печать URL для регистрации в Crypto Pay и Cardlink (после заполнения .env)."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.config import settings  # noqa: E402


def main() -> None:
    base = (settings.webhook_base_url or "").strip().rstrip("/")
    if not base:
        print("Задайте WEBHOOK_BASE_URL в .env (HTTPS в продакшене).", file=sys.stderr)
        sys.exit(1)
    crypto_path = (settings.crypto_webhook_path or "").strip()
    if not crypto_path.startswith("/"):
        crypto_path = "/" + crypto_path
    card_path = (settings.cardlink_webhook_path or "").strip()
    if not card_path.startswith("/"):
        card_path = "/" + card_path
    print("Зарегистрируйте в кабинетах платежей:")
    print(f"  Crypto Pay webhook: {base}{crypto_path}")
    print(f"  Cardlink Result URL: {base}{card_path}")
    sub_base = (settings.public_api_base_url or settings.webhook_base_url or "").strip().rstrip("/")
    print(f"  Пример ссылки Happ (после /start и оплаты, токен в профиле): {sub_base}/sub/<token>")


if __name__ == "__main__":
    main()
