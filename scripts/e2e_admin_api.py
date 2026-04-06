"""Проверка /admin/api/* при заданных ADMIN_API_KEY и запущенном uvicorn."""

import argparse
import os
import sys

import httpx


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=os.environ.get("BACKEND_URL", "http://127.0.0.1:8000"))
    p.add_argument("--key", default=os.environ.get("ADMIN_API_KEY", ""))
    args = p.parse_args()
    key = (args.key or "").strip()
    if not key:
        print("Задайте --key или ADMIN_API_KEY", file=sys.stderr)
        sys.exit(2)
    base = args.base.rstrip("/")
    headers = {"X-Admin-Key": key}
    paths = [
        "/admin/api/summary",
        "/admin/api/servers",
        "/admin/api/payments?days=7",
        "/admin/api/timeseries?days=31",
        "/admin/api/subscriptions/expiring",
    ]
    for path in paths:
        r = httpx.get(f"{base}{path}", headers=headers, timeout=30.0)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text}"
    print("e2e_admin_api: OK")


if __name__ == "__main__":
    main()
