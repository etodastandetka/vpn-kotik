"""Опционально: GET /health у уже запущенного uvicorn (по умолчанию http://127.0.0.1:8000)."""

import argparse
import sys

import httpx


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000/health", help="Полный URL /health")
    args = p.parse_args()
    try:
        r = httpx.get(args.url, timeout=5.0)
    except httpx.RequestError as e:
        print(f"Запрос не удался: {e}", file=sys.stderr)
        print("Поднимите API: docker compose up -d api  или  uvicorn app.main:app --host 0.0.0.0 --port 8000", file=sys.stderr)
        sys.exit(2)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    print("smoke_check:", r.json())


if __name__ == "__main__":
    main()
