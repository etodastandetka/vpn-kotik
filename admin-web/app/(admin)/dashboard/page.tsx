import { PhantomCharts, PhantomPeriodHighlight } from "@/components/PhantomCharts";
import { SectionTitle } from "@/components/SectionTitle";
import { StatCard } from "@/components/StatCard";
import { backendJson } from "@/lib/backend";

type Summary = {
  generated_at: string;
  users_total: number;
  active_subscriptions: number;
  payments_completed_24h: number;
  payments_completed_7d: number;
  payments_pending: number;
  payments_by_provider_7d: Record<string, number>;
  subscriptions_created_7d: number;
  subscriptions_expiring_3d: number;
  users_with_referrer: number;
  servers: { total: number; ok: number; warn: number; crit: number };
};

type Timeseries = {
  daily: { date: string; payments_completed: number; subscriptions_new: number }[];
  calendar_today_utc: { payments_completed: number; subscriptions_new: number };
  calendar_month_utc: { payments_completed: number; subscriptions_new: number };
  rollup: {
    last_7d_payments: number;
    last_7d_subscriptions: number;
    last_30d_payments: number;
    last_30d_subscriptions: number;
  };
};

export default async function DashboardPage() {
  let data: Summary;
  try {
    data = await backendJson<Summary>("/admin/api/summary");
  } catch (e) {
    return (
      <div className="rounded-xl border border-red-500/40 bg-red-950/40 p-6 text-red-200">
        <p className="font-medium">Не удалось загрузить дашборд</p>
        <p className="mt-2 text-sm opacity-90">{String(e)}</p>
        <p className="mt-4 text-sm text-slate-400">
          Проверьте FastAPI, <code className="text-violet-300">BACKEND_URL</code> и{" "}
          <code className="text-violet-300">ADMIN_API_KEY</code> в <code className="text-violet-300">.env.local</code>.
        </p>
      </div>
    );
  }

  let ts: Timeseries | null = null;
  let tsErr: string | null = null;
  try {
    ts = await backendJson<Timeseries>("/admin/api/timeseries?days=90");
  } catch (e) {
    tsErr = String(e);
  }

  const prov = data.payments_by_provider_7d || {};
  const r = ts?.rollup;
  const provLine = Object.entries(prov)
    .map(([k, v]) => `${k} — ${v}`)
    .join("   ");

  return (
    <div className="space-y-12">
      <header className="relative overflow-hidden rounded-2xl border border-violet-500/15 bg-gradient-to-br from-[#12081f]/90 via-[#0d0818] to-[#0a0612] p-6 ring-1 ring-violet-500/10 sm:p-8">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-violet-600/15 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-fuchsia-600/10 blur-3xl" />
        <div className="relative">
          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-violet-300/90">Phantom</p>
          <h1 className="mt-2 bg-gradient-to-r from-white via-violet-100 to-fuchsia-200 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl">
            Аналитика VPN
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Данные на {new Date(data.generated_at).toLocaleString("ru-RU", { dateStyle: "medium", timeStyle: "short" })}
          </p>
          {r ? (
            <div className="mt-6 flex flex-wrap gap-3">
              <div className="min-w-[140px] rounded-xl bg-[#06030d]/90 px-4 py-3 ring-1 ring-violet-500/20">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Последние 7 дней</p>
                <p className="mt-1 text-sm text-slate-300">
                  <span className="font-semibold text-violet-200">{r.last_7d_payments}</span> оплат ·{" "}
                  <span className="font-semibold text-fuchsia-200">{r.last_7d_subscriptions}</span> подписок
                </p>
              </div>
              <div className="min-w-[140px] rounded-xl bg-[#06030d]/90 px-4 py-3 ring-1 ring-violet-500/20">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Последние 30 дней</p>
                <p className="mt-1 text-sm text-slate-300">
                  <span className="font-semibold text-violet-200">{r.last_30d_payments}</span> оплат ·{" "}
                  <span className="font-semibold text-fuchsia-200">{r.last_30d_subscriptions}</span> подписок
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </header>

      {ts ? (
        <section className="space-y-6">
          <PhantomPeriodHighlight today={ts.calendar_today_utc} month={ts.calendar_month_utc} />
          <PhantomCharts daily={ts.daily} />
        </section>
      ) : (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5 text-amber-100/90 ring-1 ring-amber-500/20">
          <p className="font-medium">Графики недоступны</p>
          <p className="mt-2 text-sm text-amber-200/70">{tsErr ?? "Нет ответа от API аналитики."}</p>
          {tsErr?.includes("404") ? (
            <ul className="mt-4 list-inside list-disc space-y-1 text-xs text-amber-200/60">
              <li>
                Перезапустите FastAPI из папки проекта:{" "}
                <code className="text-amber-300">uvicorn app.main:app --reload --host 0.0.0.0 --port 8000</code>
              </li>
              <li>
                В <code className="text-amber-300">admin-web/.env.local</code> укажите{" "}
                <code className="text-amber-300">BACKEND_URL=http://127.0.0.1:8000</code> (API, не порт 3000)
              </li>
              <li>
                В <a className="text-violet-300 underline" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
                  /docs
                </a>{" "}
                должны быть маршруты <code className="text-amber-300">GET /admin/api/timeseries</code>
              </li>
            </ul>
          ) : null}
        </div>
      )}

      <section>
        <SectionTitle eyebrow="Показатели" title="Сводка" description="Ключевые метрики в один взгляд." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Активные периоды" value={data.active_subscriptions} tone="good" />
          <StatCard title="Пользователей в базе" value={data.users_total} />
          <StatCard title="Успешные оплаты · 24 ч" value={data.payments_completed_24h} tone="good" />
          <StatCard title="Успешные оплаты · 7 дн." value={data.payments_completed_7d} />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Ожидают оплаты" value={data.payments_pending} tone={data.payments_pending > 0 ? "warn" : "default"} />
          <StatCard title="Новые подписки · 7 дн." value={data.subscriptions_created_7d} />
          <StatCard
            title="Скоро истекут (≤3 дн.)"
            value={data.subscriptions_expiring_3d}
            tone={data.subscriptions_expiring_3d > 0 ? "warn" : "default"}
          />
          <StatCard title="Пришли по рефералке" value={data.users_with_referrer} />
        </div>
      </section>

      <section>
        <SectionTitle eyebrow="Инфраструктура и биллинг" title="Дополнительно" />
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-500/15 bg-[#0d0818]/70 p-6 ring-1 ring-violet-500/10">
            <h3 className="text-sm font-medium text-violet-200">Узлы</h3>
            <p className="mt-1 text-xs text-slate-500">Мониторинг — раздел «Серверы».</p>
            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              <span className="text-slate-400">
                всего <strong className="text-white">{data.servers.total}</strong>
              </span>
              <span className="text-emerald-400/90">ok {data.servers.ok}</span>
              <span className="text-amber-400/90">warn {data.servers.warn}</span>
              <span className="text-red-400/90">crit {data.servers.crit}</span>
            </div>
            <p className="mt-4 text-xs leading-relaxed text-slate-500">
              В API: <code className="text-violet-400/80">PROMETHEUS_BASE_URL</code>,{" "}
              <code className="text-violet-400/80">MONITOR_NODES_JSON</code>.
            </p>
          </div>
          <div className="rounded-2xl border border-fuchsia-500/15 bg-[#0d0818]/70 p-6 ring-1 ring-fuchsia-500/10">
            <h3 className="text-sm font-medium text-fuchsia-200">Провайдеры · 7 дн.</h3>
            <p className="mt-1 text-xs text-slate-500">Только завершённые оплаты.</p>
            <p className="mt-4 font-mono text-sm leading-relaxed text-slate-300">{provLine || "—"}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
