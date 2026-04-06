export function SectionTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-5 border-b border-violet-500/10 pb-4">
      {eyebrow ? (
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-violet-400/70">{eyebrow}</p>
      ) : null}
      <h2 className="mt-1 text-lg font-semibold tracking-tight text-white">{title}</h2>
      {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
    </div>
  );
}
