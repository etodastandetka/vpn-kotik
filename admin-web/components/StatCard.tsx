export function StatCard({
  title,
  value,
  hint,
  tone = "default",
}: {
  title: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "good" | "warn" | "bad";
}) {
  const ring =
    tone === "good"
      ? "ring-emerald-500/35 shadow-emerald-950/20"
      : tone === "warn"
        ? "ring-amber-500/35 shadow-amber-950/20"
        : tone === "bad"
          ? "ring-red-500/35 shadow-red-950/20"
          : "ring-violet-500/20 shadow-violet-950/10";
  return (
    <div
      className={`rounded-2xl border border-violet-500/10 bg-[#0d0818]/85 p-5 shadow-lg ring-1 backdrop-blur-sm ${ring}`}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-violet-300/50">{title}</p>
      <p className="mt-2 text-3xl font-semibold tabular-nums tracking-tight text-white">{value}</p>
      {hint ? <p className="mt-2 text-sm text-slate-500">{hint}</p> : null}
    </div>
  );
}
