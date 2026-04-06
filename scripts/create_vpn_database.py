"""
Создаёт пустую БД vpn (подключаясь к postgres).
Запуск из корня проекта: python scripts/create_vpn_database.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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
    c.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = c.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'vpn'")
    if cur.fetchone():
        print("База 'vpn' уже существует.")
    else:
        cur.execute('CREATE DATABASE vpn')
        print("База 'vpn' создана.")
    cur.close()
    c.close()


if __name__ == "__main__":
    main()
