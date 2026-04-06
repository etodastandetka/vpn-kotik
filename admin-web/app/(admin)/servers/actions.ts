"use server";

import { revalidatePath } from "next/cache";

import { backendFetch } from "@/lib/backend";

export type FormMessage = { error: string | null };

export async function addMonitorNode(_prev: FormMessage, formData: FormData): Promise<FormMessage> {
  const name = String(formData.get("name") ?? "").trim();
  const instance = String(formData.get("instance") ?? "").trim();
  const node_key = String(formData.get("node_key") ?? "").trim();
  const panel_health_url = String(formData.get("panel_health_url") ?? "").trim();

  if (!name || !instance) {
    return { error: "Заполните имя и instance (host:port для Prometheus)." };
  }

  const body: Record<string, string> = { name, instance };
  if (node_key) body.node_key = node_key;
  if (panel_health_url) body.panel_health_url = panel_health_url;

  const r = await backendFetch("/admin/api/servers", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const t = await r.text();
    return { error: `${r.status} ${t}` };
  }

  revalidatePath("/servers");
  revalidatePath("/dashboard");
  return { error: null };
}

export async function deleteMonitorNode(_prev: FormMessage, formData: FormData): Promise<FormMessage> {
  const node_key = String(formData.get("node_key") ?? "").trim();
  if (!node_key) {
    return { error: "Нет id узла." };
  }

  const r = await backendFetch(`/admin/api/servers/${encodeURIComponent(node_key)}`, {
    method: "DELETE",
  });

  if (!r.ok) {
    const t = await r.text();
    return { error: `${r.status} ${t}` };
  }

  revalidatePath("/servers");
  revalidatePath("/dashboard");
  return { error: null };
}
