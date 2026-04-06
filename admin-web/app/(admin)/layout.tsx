import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AdminNav } from "@/components/AdminNav";
import { SESSION_COOKIE, verifySessionCookie } from "@/lib/session";

export default function AdminGroupLayout({ children }: { children: React.ReactNode }) {
  const c = cookies().get(SESSION_COOKIE);
  if (!verifySessionCookie(c?.value)) {
    redirect("/login");
  }
  return (
    <div className="min-h-screen">
      <AdminNav />
      <main className="mx-auto max-w-6xl px-4 py-10">{children}</main>
    </div>
  );
}
