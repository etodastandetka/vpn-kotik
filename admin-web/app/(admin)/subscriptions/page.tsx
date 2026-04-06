import { backendJson } from "@/lib/backend";

type Item = {
  subscription_id: number;
  telegram_id: number;
  plan_id: string;
  expires_at: string;
};

export default async function SubscriptionsPage() {
  let data: { within_days: number; items: Item[] };
  try {
    data = await backendJson("/admin/api/subscriptions/expiring?within_days=14&limit=80");
  } catch (e) {
    return <div className="text-red-300">Ошибка: {String(e)}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Скоро истекают</h2>
        <p className="mt-1 text-sm text-slate-500">
          Подписки, которые закончатся в ближайшие {data.within_days} дн.
        </p>
      </div>
      <div className="overflow-hidden rounded-2xl border border-slate-700/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Telegram ID</th>
              <th className="px-4 py-3">План</th>
              <th className="px-4 py-3">Истекает</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950/40">
            {data.items.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                  Нет записей
                </td>
              </tr>
            ) : (
              data.items.map((r) => (
                <tr key={r.subscription_id} className="text-slate-300">
                  <td className="px-4 py-3 font-mono">{r.telegram_id}</td>
                  <td className="px-4 py-3 font-mono">{r.plan_id}</td>
                  <td className="px-4 py-3">{new Date(r.expires_at).toLocaleString("ru-RU")}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
