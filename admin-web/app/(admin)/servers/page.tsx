import { StatusBadge } from "@/components/StatusBadge";
import { backendJson } from "@/lib/backend";

import { AddNodeForm, DeleteNodeForm } from "./ManageNodesForms";

type Snap = {
  id: string;
  name: string;
  instance: string;
  panel_health_url: string | null;
  up: boolean | null;
  cpu_pct: number | null;
  mem_pct: number | null;
  disk_pct: number | null;
  net_rx_mbps: number | null;
  net_tx_mbps: number | null;
  panel_ok: boolean | null;
  status: string;
  prometheus_error: string | null;
};

type ServersPayload = { items: Snap[]; nodes_source?: "database" | "env" };

export default async function ServersPage() {
  let data: ServersPayload;
  try {
    data = await backendJson<ServersPayload>("/admin/api/servers");
  } catch (e) {
    return (
      <div className="rounded-xl border border-red-500/40 bg-red-950/40 p-6 text-red-200">
        Ошибка: {String(e)}
      </div>
    );
  }

  const { items, nodes_source: nodesSourceRaw } = data;
  const nodes_source = nodesSourceRaw ?? "env";
  const fmt = (n: number | null, d = 1) => (n == null ? "—" : `${n.toFixed(d)}`);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Серверы</h2>
        <p className="mt-1 text-sm text-slate-500">
          Метрики из Prometheus (node_exporter). Сначала узлы с проблемами.
        </p>
        <p className="mt-3 text-xs text-slate-400">
          {nodes_source === "database" ? (
            <>
              Список узлов хранится в <strong className="text-slate-300">базе данных</strong> — добавление и удаление ниже
              меняют мониторинг без правки <code className="text-violet-400">MONITOR_NODES_JSON</code>.
            </>
          ) : (
            <>
              Сейчас узлы берутся из <code className="text-violet-400">MONITOR_NODES_JSON</code> в окружении API. Как только вы
              добавите хотя бы один узел через форму, будет использоваться только <strong className="text-slate-300">база</strong>.
            </>
          )}
        </p>
      </div>

      <AddNodeForm />

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="text-slate-500">Нет узлов: заполните JSON в .env или добавьте сервер выше.</p>
        ) : (
          items.map((s) => (
            <div
              key={s.id}
              className="rounded-2xl border border-slate-700/80 bg-slate-900/50 p-5 shadow-lg shadow-black/10"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-medium text-white">{s.name}</h3>
                  <p className="mt-1 font-mono text-xs text-slate-500">{s.instance}</p>
                  <p className="mt-1 font-mono text-[11px] text-slate-600">id: {s.id}</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <StatusBadge status={s.status} />
                  {nodes_source === "database" ? <DeleteNodeForm nodeKey={s.id} /> : null}
                </div>
              </div>
              <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <span className="text-slate-500">CPU %</span>
                  <p className="font-mono text-slate-200">{fmt(s.cpu_pct)}</p>
                </div>
                <div>
                  <span className="text-slate-500">RAM %</span>
                  <p className="font-mono text-slate-200">{fmt(s.mem_pct)}</p>
                </div>
                <div>
                  <span className="text-slate-500">Disk %</span>
                  <p className="font-mono text-slate-200">{fmt(s.disk_pct)}</p>
                </div>
                <div>
                  <span className="text-slate-500">Net RX / TX</span>
                  <p className="font-mono text-slate-200">
                    {fmt(s.net_rx_mbps)} / {fmt(s.net_tx_mbps)} Mbit/s
                  </p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                <span>up (prom): {s.up == null ? "?" : s.up ? "да" : "нет"}</span>
                <span>
                  панель:{" "}
                  {s.panel_health_url
                    ? s.panel_ok == null
                      ? "—"
                      : s.panel_ok
                        ? "OK"
                        : "fail"
                    : "не задан URL"}
                </span>
              </div>
              {s.prometheus_error ? (
                <p className="mt-2 text-xs text-amber-400">{s.prometheus_error}</p>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
