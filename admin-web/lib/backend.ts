const base = () => (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function backendFetch(path: string, init?: RequestInit): Promise<Response> {
  const key = (process.env.ADMIN_API_KEY || "").trim();
  if (!key) {
    return new Response(JSON.stringify({ error: "ADMIN_API_KEY is not set on admin-web" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
  const url = `${base()}${path.startsWith("/") ? path : `/${path}`}`;
  return fetch(url, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
      "X-Admin-Key": key,
    },
  });
}

export async function backendJson<T>(path: string): Promise<T> {
  const r = await backendFetch(path);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${t}`);
  }
  return r.json() as Promise<T>;
}
