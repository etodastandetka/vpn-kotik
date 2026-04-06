import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE, verifySessionCookie } from "@/lib/session";

export default function HomePage() {
  const c = cookies().get(SESSION_COOKIE);
  if (verifySessionCookie(c?.value)) {
    redirect("/dashboard");
  }
  redirect("/login");
}
