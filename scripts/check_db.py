"""Одноразовая проверка: есть ли БД vpn. Запуск из корня проекта: python scripts/check_db.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from sqlalchemy.engine.url import make_url

from app.config import settings


def main() -> None:
    u2 = make_url(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
    c = psycopg2.connect(
        dbname="postgres",
        user=u2.username,
        password=u2.password,
        host=u2.host,
        port=u2.port or 5432,
    )
    cur = c.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY 1")
    print("Databases:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'vpn'")
    print("Database 'vpn' exists:", cur.fetchone() is not None)
    c.close()


if __name__ == "__main__":
    main()
