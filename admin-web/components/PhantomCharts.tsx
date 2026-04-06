"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type DailyPoint = {
  date: string;
  payments_completed: number;
  subscriptions_new: number;
};

type Range = 7 | 30 | 90;
type ChartMode = "line" | "area" | "bar";

const ranges: { id: Range; label: string }[] = [
  { id: 7, label: "7 дн." },
  { id: 30, label: "30 дн." },
  { id: 90, label: "90 дн." },
];

const modes: { id: ChartMode; label: string }[] = [
  { id: "line", label: "График" },
  { id: "area", label: "С заливкой" },
  { id: "bar", label: "Столбцы" },
];

function shortDate(iso: string) {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}`;
}

function ruDate(iso: string) {
  try {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
      year: y !== new Date().getFullYear() ? "2-digit" : undefined,
    });
  } catch {
    return iso;
  }
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: DailyPoint & { label: string }; color: string; name: string; value: number }>;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-xl border border-violet-500/35 bg-[#0d0818]/95 px-4 py-3 shadow-xl shadow-violet-950/50 backdrop-blur-sm">
      <p className="text-xs font-medium text-violet-200">{ruDate(row.date)}</p>
      <div className="mt-2 space-y-1.5 text-sm">
        {payload.map((p) => (
          <div key={p.name} className="flex items-center justify-between gap-6">
            <span className="flex items-center gap-2 text-slate-300">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: p.color }} />
              {p.name}
            </span>
            <span className="font-mono font-semibold tabular-nums text-white">{p.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PhantomCharts({ daily }: { daily: DailyPoint[] }) {
  const [range, setRange] = useState<Range>(30);
  const [mode, setMode] = useState<ChartMode>("line");

  const data = useMemo(
    () => daily.slice(-range).map((p) => ({ ...p, label: shortDate(p.date) })),
    [daily, range],
  );

  const maxVal = useMemo(() => {
    let m = 1;
    for (const p of data) {
      m = Math.max(m, p.payments_completed, p.subscriptions_new);
    }
    return m + Math.max(1, Math.ceil(m * 0.12));
  }, [data]);

  const axisCommon = (
    <>
      <CartesianGrid strokeDasharray="4 6" stroke="rgba(139, 92, 246, 0.14)" vertical={false} />
      <XAxis
        dataKey="label"
        height={36}
        tick={{ fill: "#a8a8c0", fontSize: 11 }}
        tickLine={{ stroke: "rgba(139,92,246,0.25)" }}
        axisLine={{ stroke: "rgba(139,92,246,0.35)" }}
        interval={range <= 7 ? 0 : range <= 30 ? "preserveStartEnd" : Math.floor(range / 12)}
        label={{ value: "Дата (день, UTC)", position: "insideBottom", offset: -4, fill: "#6b5a8c", fontSize: 11 }}
      />
      <YAxis
        tick={{ fill: "#a8a8c0", fontSize: 11 }}
        tickLine={false}
        axisLine={{ stroke: "rgba(139,92,246,0.35)" }}
        allowDecimals={false}
        domain={[0, maxVal]}
        label={{
          value: "Штук за день",
          angle: -90,
          position: "insideLeft",
          style: { fill: "#6b5a8c", fontSize: 11 },
        }}
      />
      <Tooltip content={<ChartTooltip />} cursor={{ stroke: "rgba(167, 139, 250, 0.35)", strokeWidth: 1 }} />
      <Legend
        wrapperStyle={{ paddingTop: 20 }}
        formatter={(value) => <span className="text-sm text-slate-300">{value}</span>}
      />
    </>
  );

  const lineDots = {
    r: 4,
    strokeWidth: 2,
    stroke: "#0d0818",
  } as const;

  return (
    <div className="phantom-glow rounded-3xl border border-violet-500/20 bg-[#0d0818]/90 p-6 shadow-2xl shadow-violet-950/50 backdrop-blur-sm sm:p-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-violet-300/90">По дням (UTC)</h3>
          <p className="mt-1 max-w-md text-sm text-slate-400">
            Фиолетовая линия — успешные оплаты, розовая — новые подписки в базе. Дни в UTC.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="flex flex-wrap gap-1.5 rounded-2xl bg-[#06030d]/80 p-1 ring-1 ring-violet-500/20">
            {ranges.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setRange(t.id)}
                className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                  range === t.id
                    ? "bg-violet-600 text-white shadow-md shadow-violet-600/35"
                    : "text-violet-200/75 hover:bg-violet-950/90 hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-1.5 rounded-2xl bg-[#06030d]/80 p-1 ring-1 ring-fuchsia-500/15">
            {modes.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMode(m.id)}
                className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                  mode === m.id
                    ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md shadow-fuchsia-600/25"
                    : "text-fuchsia-100/70 hover:bg-fuchsia-950/50 hover:text-white"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="relative mt-8 min-h-[340px] w-full sm:min-h-[400px] lg:min-h-[440px]">
        <div className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-b from-violet-500/[0.06] to-transparent" />
        <ResponsiveContainer width="100%" height="100%" minHeight={340}>
          {mode === "line" ? (
            <LineChart data={data} margin={{ top: 16, right: 16, left: 4, bottom: 28 }}>
              {axisCommon}
              <Line
                type="natural"
                dataKey="payments_completed"
                name="Оплаты"
                stroke="#a78bfa"
                strokeWidth={3}
                dot={{ fill: "#8b5cf6", ...lineDots }}
                activeDot={{ r: 8, fill: "#c4b5fd", stroke: "#fff", strokeWidth: 2 }}
                isAnimationActive
              />
              <Line
                type="natural"
                dataKey="subscriptions_new"
                name="Подписки"
                stroke="#f472b6"
                strokeWidth={3}
                dot={{ fill: "#db2777", ...lineDots }}
                activeDot={{ r: 8, fill: "#fbcfe8", stroke: "#fff", strokeWidth: 2 }}
                isAnimationActive
              />
            </LineChart>
          ) : mode === "area" ? (
            <AreaChart data={data} margin={{ top: 16, right: 16, left: 4, bottom: 28 }}>
              <defs>
                <linearGradient id="phPay" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.85} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="phSub" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#e879f9" stopOpacity={0.75} />
                  <stop offset="100%" stopColor="#e879f9" stopOpacity={0} />
                </linearGradient>
              </defs>
              {axisCommon}
              <Area
                type="natural"
                dataKey="payments_completed"
                name="Оплаты"
                stroke="#c4b5fd"
                strokeWidth={2}
                fill="url(#phPay)"
              />
              <Area
                type="natural"
                dataKey="subscriptions_new"
                name="Подписки"
                stroke="#f9a8d4"
                strokeWidth={2}
                fill="url(#phSub)"
              />
            </AreaChart>
          ) : (
            <BarChart data={data} margin={{ top: 16, right: 16, left: 4, bottom: 28 }} barGap={4} barCategoryGap="12%">
              {axisCommon}
              <Bar dataKey="payments_completed" name="Оплаты" fill="#8b5cf6" radius={[8, 8, 0, 0]} maxBarSize={36} />
              <Bar dataKey="subscriptions_new" name="Подписки" fill="#d946ef" radius={[8, 8, 0, 0]} maxBarSize={36} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function PeriodCard({
  title,
  pay,
  sub,
  accent,
}: {
  title: string;
  pay: number;
  sub: number;
  accent: "violet" | "fuchsia";
}) {
  const border = accent === "violet" ? "border-violet-500/25 ring-violet-500/10" : "border-fuchsia-500/20 ring-fuchsia-500/10";
  const grad =
    accent === "violet"
      ? "from-violet-950/60 to-[#0d0818]"
      : "from-[#18081f] to-violet-950/40";
  const label = accent === "violet" ? "text-violet-300/80" : "text-fuchsia-300/80";

  return (
    <div className={`rounded-2xl border bg-gradient-to-br p-6 ring-1 ${border} ${grad}`}>
      <p className={`text-xs font-semibold uppercase tracking-wider ${label}`}>{title}</p>
      <div className="mt-5 grid grid-cols-2 gap-6">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Оплаты</p>
          <p className="mt-1 text-3xl font-bold tabular-nums text-white">{pay}</p>
        </div>
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Подписки</p>
          <p className="mt-1 text-3xl font-bold tabular-nums text-fuchsia-200">{sub}</p>
        </div>
      </div>
    </div>
  );
}

export function PhantomPeriodHighlight({
  today,
  month,
}: {
  today: { payments_completed: number; subscriptions_new: number };
  month: { payments_completed: number; subscriptions_new: number };
}) {
  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-2">
        <PeriodCard title="Сегодня · UTC" pay={today.payments_completed} sub={today.subscriptions_new} accent="violet" />
        <PeriodCard title="Этот месяц · UTC" pay={month.payments_completed} sub={month.subscriptions_new} accent="fuchsia" />
      </div>
      <p className="mt-3 text-center text-[11px] text-slate-500">
        Оплаты — только со статусом «завершено»; подписки — новые записи в таблице.
      </p>
    </div>
  );
}
