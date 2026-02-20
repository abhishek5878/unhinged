import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getUserProfile(token: string) {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { getToken } = await auth();
  const token = await getToken();

  if (!token) {
    redirect("/sign-in");
  }

  const profile = await getUserProfile(token);

  return (
    <AppShell profile={{ email: profile?.email, name: profile?.name }}>
      <ErrorBoundary>{children}</ErrorBoundary>
    </AppShell>
  );
}
