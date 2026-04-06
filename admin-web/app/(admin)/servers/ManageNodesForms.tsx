"use client";

import { useFormState, useFormStatus } from "react-dom";

import { addMonitorNode, deleteMonitorNode, type FormMessage } from "./actions";

const initial: FormMessage = { error: null };

function SubmitButton({ label, pendingLabel }: { label: string; pendingLabel: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-violet-500 disabled:opacity-50"
    >
      {pending ? pendingLabel : label}
    </button>
  );
}

export function AddNodeForm() {
  const [state, formAction] = useFormState(addMonitorNode, initial);

  return (
    <form action={formAction} className="space-y-3 rounded-2xl border border-slate-700/80 bg-slate-900/50 p-5">
      <h3 className="text-sm font-medium text-white">Добавить сервер</h3>
      <p className="text-xs text-slate-500">
        Если IP заблокировали — удалите старый узел и добавьте новый с актуальным <code className="text-violet-400">instance</code>{" "}
        (как в Prometheus, обычно <code className="text-violet-400">1.2.3.4:9100</code>).
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-xs text-slate-400">
          Имя
          <input
            name="name"
            required
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            placeholder="NL-1"
          />
        </label>
        <label className="block text-xs text-slate-400">
          Id узла (необязательно)
          <input
            name="node_key"
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            placeholder="авто из instance"
          />
        </label>
        <label className="block text-xs text-slate-400 sm:col-span-2">
          Instance (Prometheus)
          <input
            name="instance"
            required
            className="mt-1 w-full font-mono text-sm text-white rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="203.0.113.10:9100"
          />
        </label>
        <label className="block text-xs text-slate-400 sm:col-span-2">
          URL проверки панели (необязательно)
          <input
            name="panel_health_url"
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            placeholder="https://panel.example/health"
          />
        </label>
      </div>
      {state.error ? <p className="text-sm text-red-400">{state.error}</p> : null}
      <SubmitButton label="Добавить" pendingLabel="Добавляем…" />
    </form>
  );
}

export function DeleteNodeForm({ nodeKey }: { nodeKey: string }) {
  const [state, formAction] = useFormState(deleteMonitorNode, initial);

  return (
    <form action={formAction} className="inline-flex flex-col items-end gap-1">
      <input type="hidden" name="node_key" value={nodeKey} />
      <button
        type="submit"
        className="rounded-lg border border-red-500/50 bg-red-950/40 px-3 py-1.5 text-xs text-red-200 hover:bg-red-950/70"
      >
        Удалить из мониторинга
      </button>
      {state.error ? <span className="max-w-xs text-right text-xs text-red-400">{state.error}</span> : null}
    </form>
  );
}
