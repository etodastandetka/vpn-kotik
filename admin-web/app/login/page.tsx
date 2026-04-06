"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const r = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        setErr((data as { error?: string }).error || "Ошибка входа");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="phantom-glow w-full max-w-md rounded-2xl border border-violet-500/25 bg-[#0d0818]/90 p-8 shadow-2xl ring-1 ring-violet-500/20 backdrop-blur-md">
        <p className="text-center text-xs font-bold uppercase tracking-[0.3em] text-violet-400/90">Phantom</p>
        <h1 className="mt-2 text-center text-xl font-bold text-white">VPN Admin</h1>
        <p className="mt-2 text-center text-sm text-slate-500">Введите пароль дашборда</p>
        <form onSubmit={onSubmit} className="mt-8 space-y-4">
          <input
            type="password"
            autoComplete="current-password"
            className="w-full rounded-xl border border-violet-500/30 bg-[#06030d]/90 px-4 py-3 text-white outline-none ring-0 transition placeholder:text-slate-600 focus:border-violet-400 focus:ring-1 focus:ring-violet-500/40"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {err ? <p className="text-sm text-red-400">{err}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-600/30 transition hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-50"
          >
            {loading ? "…" : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}
