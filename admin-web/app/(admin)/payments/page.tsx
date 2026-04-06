import { backendJson } from "@/lib/backend";

type Row = { provider: string; status: string; count: number };

export default async function PaymentsPage() {
  let data: { since: string; days: number; breakdown: Row[] };
  try {
    data = await backendJson("/admin/api/payments?days=7");
  } catch (e) {
    return <div className="text-red-300">Ошибка: {String(e)}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Платежи</h2>
        <p className="mt-1 text-sm text-slate-500">
          За последние {data.days} дн. с {new Date(data.since).toLocaleString("ru-RU")}
        </p>
      </div>
      <div className="overflow-hidden rounded-2xl border border-slate-700/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Провайдер</th>
              <th className="px-4 py-3">Статус</th>
              <th className="px-4 py-3 text-right">Кол-во</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950/40">
            {data.breakdown.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                  Нет данных
                </td>
              </tr>
            ) : (
              data.breakdown.map((r, i) => (
                <tr key={i} className="text-slate-300">
                  <td className="px-4 py-3 font-mono">{r.provider}</td>
                  <td className="px-4 py-3">{r.status}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{r.count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
