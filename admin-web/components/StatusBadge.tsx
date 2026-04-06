export function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const cls =
    s === "ok"
      ? "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40"
      : s === "warn"
        ? "bg-amber-500/15 text-amber-200 ring-amber-500/40"
        : s === "crit"
          ? "bg-red-500/15 text-red-300 ring-red-500/40"
          : "bg-slate-500/15 text-slate-300 ring-slate-500/40";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ring-1 ${cls}`}>
      {status}
    </span>
  );
}
