import Link from "next/link";

const links = [
  { href: "/dashboard", label: "Дашборд" },
  { href: "/servers", label: "Серверы" },
  { href: "/payments", label: "Платежи" },
  { href: "/subscriptions", label: "Подписки" },
];

export function AdminNav() {
  return (
    <header className="border-b border-violet-500/15 bg-[#0a0612]/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
        <div className="flex items-center gap-3">
          <span className="rounded-lg bg-violet-600/25 px-2.5 py-1 text-xs font-bold uppercase tracking-[0.15em] text-violet-200 shadow-lg shadow-violet-600/20">
            Phantom
          </span>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white">VPN · консоль</h1>
          </div>
        </div>
        <nav className="flex flex-wrap gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="rounded-lg px-3 py-2 text-sm text-violet-100/75 transition hover:bg-violet-950/80 hover:text-white"
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/api/logout"
            className="rounded-lg px-3 py-2 text-sm text-slate-500 transition hover:bg-red-950/40 hover:text-red-300"
          >
            Выход
          </Link>
        </nav>
      </div>
    </header>
  );
}
