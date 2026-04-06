import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  dashboardPassword,
  expectedSessionToken,
  sessionSecret,
} from "@/lib/session";

export async function POST(req: Request) {
  if (!sessionSecret() || !dashboardPassword()) {
    return NextResponse.json(
      { error: "Задайте ADMIN_SESSION_SECRET и ADMIN_DASHBOARD_PASSWORD в .env.local" },
      { status: 503 },
    );
  }
  let body: { password?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
  const password = (body.password || "").trim();
  if (password !== dashboardPassword()) {
    return NextResponse.json({ error: "Неверный пароль" }, { status: 401 });
  }
  const token = expectedSessionToken();
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return res;
}
