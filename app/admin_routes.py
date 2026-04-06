from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import async_session_maker
from app.models import AdminMonitorNode
from app.services import admin_analytics, monitoring

router = APIRouter(prefix="/admin/api", tags=["admin"])


class MonitorNodeCreateBody(BaseModel):
    node_key: str | None = Field(None, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    instance: str = Field(..., min_length=1, max_length=256)
    panel_health_url: str | None = Field(None, max_length=512)

    def normalized_instance(self) -> str:
        return self.instance.strip()

    def resolved_node_key(self) -> str:
        raw = (self.node_key or "").strip()
        if raw:
            return raw[:64]
        return monitoring.default_node_key_from_instance(self.normalized_instance())

    def normalized_panel(self) -> str | None:
        u = (self.panel_health_url or "").strip()
        return u or None


def require_admin_key(x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None) -> None:
    expected = (settings.admin_api_key or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_API_KEY is not configured")
    if not x_admin_key or x_admin_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin key")


@router.get("/summary")
async def admin_summary(_: None = Depends(require_admin_key)) -> dict:
    async with async_session_maker() as session:
        db = await admin_analytics.dashboard_summary(session)
        servers = await monitoring.fetch_all_nodes(session)
    crit = sum(1 for s in servers if s.get("status") == "crit")
    warn = sum(1 for s in servers if s.get("status") == "warn")
    ok = sum(1 for s in servers if s.get("status") == "ok")
    return {
        **db,
        "servers": {
            "total": len(servers),
            "ok": ok,
            "warn": warn,
            "crit": crit,
        },
    }


@router.get("/servers")
async def admin_servers(_: None = Depends(require_admin_key)) -> dict:
    async with async_session_maker() as session:
        n = await session.scalar(select(func.count()).select_from(AdminMonitorNode))
        items = await monitoring.fetch_all_nodes(session)
    return {"items": items, "nodes_source": "database" if (n or 0) > 0 else "env"}


@router.post("/servers")
async def admin_servers_create(
    body: MonitorNodeCreateBody,
    _: None = Depends(require_admin_key),
) -> dict:
    inst = body.normalized_instance()
    if not inst:
        raise HTTPException(status_code=400, detail="instance is empty")
    nk = body.resolved_node_key()
    panel = body.normalized_panel()
    row = AdminMonitorNode(
        node_key=nk,
        name=body.name.strip(),
        instance=inst,
        panel_health_url=panel,
    )
    async with async_session_maker() as session:
        session.add(row)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Узел с таким id (node_key) уже есть — задайте другой id или удалите старый.",
            ) from None
    return {"ok": True, "node_key": nk}


@router.delete("/servers/{node_key}")
async def admin_servers_delete(
    node_key: str,
    _: None = Depends(require_admin_key),
) -> dict:
    nk = node_key.strip()
    if not nk:
        raise HTTPException(status_code=400, detail="node_key is empty")
    async with async_session_maker() as session:
        res = await session.execute(delete(AdminMonitorNode).where(AdminMonitorNode.node_key == nk))
        await session.commit()
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Узел не найден в базе (уже удалён?)")
    return {"ok": True}


@router.get("/payments")
async def admin_payments(days: int = 7, _: None = Depends(require_admin_key)) -> dict:
    async with async_session_maker() as session:
        return await admin_analytics.payments_breakdown(session, days=days)


async def _admin_timeseries_payload(days: int) -> dict:
    async with async_session_maker() as session:
        return await admin_analytics.analytics_timeseries(session, days=days)


@router.get("/timeseries")
async def admin_timeseries(days: int = 31, _: None = Depends(require_admin_key)) -> dict:
    """Ряд по дням (короткий путь для админки)."""
    return await _admin_timeseries_payload(days)


@router.get("/analytics/timeseries")
async def admin_analytics_ts(days: int = 31, _: None = Depends(require_admin_key)) -> dict:
    """То же, что /timeseries (совместимость)."""
    return await _admin_timeseries_payload(days)


@router.get("/subscriptions/expiring")
async def admin_subs_expiring(
    within_days: int = 7,
    limit: int = 50,
    _: None = Depends(require_admin_key),
) -> dict:
    async with async_session_maker() as session:
        return await admin_analytics.subscriptions_expiring(session, within_days=within_days, limit=limit)
