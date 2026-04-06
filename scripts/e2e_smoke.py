"""Локальная проверка FastAPI без поднятого uvicorn (ASGI in-process)."""

import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


async def run() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "ok", r.json()
        # /sub/... требует PostgreSQL — проверяйте вручную при поднятой БД


def main() -> None:
    asyncio.run(run())
    print("e2e_smoke: OK (/health)")


if __name__ == "__main__":
    main()
