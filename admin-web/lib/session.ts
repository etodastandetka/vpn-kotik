import { createHmac, timingSafeEqual } from "crypto";

export const SESSION_COOKIE = "vpn_admin";

export function sessionSecret(): string {
  return (process.env.ADMIN_SESSION_SECRET || process.env.ADMIN_API_KEY || "").trim();
}

export function dashboardPassword(): string {
  return (process.env.ADMIN_DASHBOARD_PASSWORD || "").trim();
}

export function expectedSessionToken(): string {
  const secret = sessionSecret();
  const password = dashboardPassword();
  if (!secret || !password) return "";
  return createHmac("sha256", secret).update(password).digest("hex");
}

export function verifySessionCookie(value: string | undefined): boolean {
  const exp = expectedSessionToken();
  if (!value || !exp) return false;
  try {
    const a = Buffer.from(value, "hex");
    const b = Buffer.from(exp, "hex");
    return a.length === b.length && timingSafeEqual(a, b);
  } catch {
    return false;
  }
}
