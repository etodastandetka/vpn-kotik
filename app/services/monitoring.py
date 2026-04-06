"""Опрос Prometheus (node_exporter) и проверка доступности панелей."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AdminMonitorNode

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MonitorNode:
    id: str
    name: str
    instance: str
    panel_health_url: str | None = None


def parse_monitor_nodes(raw: str) -> list[MonitorNode]:
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("MONITOR_NODES_JSON: невалидный JSON")
        return []
    out: list[MonitorNode] = []
    if not isinstance(data, list):
        return []
    for item in data:
        if not isinstance(item, dict):
            continue
        nid = str(item.get("id") or item.get("instance") or "").strip()
        name = str(item.get("name") or nid).strip() or nid
        inst = str(item.get("instance") or "").strip()
        if not inst:
            continue
        panel = item.get("panel_health_url")
        panel_s = str(panel).strip() if panel else None
        out.append(
            MonitorNode(
                id=nid or inst,
                name=name,
                instance=inst,
                panel_health_url=panel_s or None,
            )
        )
    return out


def default_node_key_from_instance(instance: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", instance.strip()).strip("_")
    return (s or "node")[:64]


async def list_resolved_monitor_nodes(session: AsyncSession) -> list[MonitorNode]:
    rows = (await session.scalars(select(AdminMonitorNode).order_by(AdminMonitorNode.id))).all()
    if rows:
        return [
            MonitorNode(
                id=r.node_key,
                name=r.name,
                instance=r.instance,
                panel_health_url=(r.panel_health_url.strip() or None) if r.panel_health_url else None,
            )
            for r in rows
        ]
    return parse_monitor_nodes(settings.monitor_nodes_json)


def _scalar_from_result(data: dict[str, Any], node_idx: int = 0) -> float | None:
    try:
        res = data.get("data", {}).get("result", [])
        if not res:
            return None
        val = res[node_idx].get("value", [None, None])[1]
        if val is None:
            return None
        return float(val)
    except (IndexError, TypeError, ValueError):
        return None


async def _prom_query(client: httpx.AsyncClient, query: str) -> dict[str, Any]:
    base = (settings.prometheus_base_url or "").strip().rstrip("/")
    r = await client.get(f"{base}/api/v1/query", params={"query": query})
    r.raise_for_status()
    return r.json()


def _status_for_metrics(
    *,
    up_ok: bool | None,
    cpu: float | None,
    mem: float | None,
    disk: float | None,
) -> str:
    if up_ok is False:
        return "crit"
    warn = False
    thr_c = settings.monitor_cpu_warn_pct
    thr_m = settings.monitor_mem_warn_pct
    thr_d = settings.monitor_disk_warn_pct
    if cpu is not None and cpu >= thr_c:
        warn = True
    if mem is not None and mem >= thr_m:
        warn = True
    if disk is not None and disk >= thr_d:
        warn = True
    if warn:
        return "warn"
    if up_ok is True or cpu is not None or mem is not None:
        return "ok"
    return "unknown"


async def panel_reachable(url: str) -> bool | None:
    if not url:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=settings.monitor_panel_timeout_sec,
            follow_redirects=True,
        ) as client:
            r = await client.get(url, headers={"User-Agent": "VPN-Admin-Health/1.0"})
            return r.status_code < 500
    except httpx.HTTPError:
        log.debug("panel health failed for %s", url, exc_info=True)
        return False


async def fetch_node_snapshot(node: MonitorNode) -> dict[str, Any]:
    base = (settings.prometheus_base_url or "").strip()
    out: dict[str, Any] = {
        "id": node.id,
        "name": node.name,
        "instance": node.instance,
        "panel_health_url": node.panel_health_url,
        "up": None,
        "cpu_pct": None,
        "mem_pct": None,
        "disk_pct": None,
        "net_rx_mbps": None,
        "net_tx_mbps": None,
        "panel_ok": None,
        "status": "unknown",
        "prometheus_error": None,
    }

    if node.panel_health_url:
        out["panel_ok"] = await panel_reachable(node.panel_health_url)

    if not base:
        out["prometheus_error"] = "PROMETHEUS_BASE_URL не задан"
        out["status"] = _status_for_metrics(
            up_ok=out["panel_ok"] if node.panel_health_url else None,
            cpu=None,
            mem=None,
            disk=None,
        )
        if out["status"] == "unknown" and out["panel_ok"] is False:
            out["status"] = "crit"
        elif out["status"] == "unknown" and out["panel_ok"] is True:
            out["status"] = "ok"
        return out

    inst = node.instance.replace('"', '\\"')
    timeout = settings.prometheus_timeout_sec

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            up_q = f'up{{instance="{inst}"}}'
            cpu_q = (
                '(1 - avg(rate(node_cpu_seconds_total{mode="idle",instance="'
                + inst
                + '"}[5m]))) * 100'
            )
            mem_q = (
                '(1 - (node_memory_MemAvailable_bytes{instance="'
                + inst
                + '"} / node_memory_MemTotal_bytes{instance="'
                + inst
                + '"})) * 100'
            )
            disk_q = (
                '100 * (1 - max(node_filesystem_avail_bytes{instance="'
                + inst
                + '",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{instance="'
                + inst
                + '",fstype!~"tmpfs|overlay"}))'
            )
            net_rx_q = (
                'sum(rate(node_network_receive_bytes_total{instance="'
                + inst
                + '",device!="lo"}[5m])) * 8 / 1e6'
            )
            net_tx_q = (
                'sum(rate(node_network_transmit_bytes_total{instance="'
                + inst
                + '",device!="lo"}[5m])) * 8 / 1e6'
            )

            up_json = await _prom_query(client, up_q)
            cpu_json = await _prom_query(client, cpu_q)
            mem_json = await _prom_query(client, mem_q)
            disk_json = await _prom_query(client, disk_q)
            rx_json = await _prom_query(client, net_rx_q)
            tx_json = await _prom_query(client, net_tx_q)

            status_up = up_json.get("status")
            if status_up != "success":
                out["prometheus_error"] = up_json.get("error") or "query failed"
                up_val = None
            else:
                up_val = _scalar_from_result(up_json)
                out["up"] = (up_val or 0) >= 1

            if up_json.get("status") == "success":
                out["cpu_pct"] = _scalar_from_result(cpu_json)
                out["mem_pct"] = _scalar_from_result(mem_json)
                out["disk_pct"] = _scalar_from_result(disk_json)
                out["net_rx_mbps"] = _scalar_from_result(rx_json)
                out["net_tx_mbps"] = _scalar_from_result(tx_json)

    except httpx.HTTPError as e:
        out["prometheus_error"] = str(e)
        out["up"] = False

    out["status"] = _status_for_metrics(
        up_ok=out["up"],
        cpu=out["cpu_pct"],
        mem=out["mem_pct"],
        disk=out["disk_pct"],
    )
    if out["panel_ok"] is False:
        out["status"] = "crit"
    return out


async def fetch_all_nodes(session: AsyncSession) -> list[dict[str, Any]]:
    nodes = await list_resolved_monitor_nodes(session)
    snapshots = [await fetch_node_snapshot(n) for n in nodes]
    order = {"crit": 0, "warn": 1, "unknown": 2, "ok": 3}
    snapshots.sort(key=lambda x: order.get(str(x.get("status")), 9))
    return snapshots
