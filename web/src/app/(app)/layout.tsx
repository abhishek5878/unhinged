import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

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

  // If user has no shadow vector, redirect to onboarding
  // (but don't redirect if they're already on the onboarding page)
  if (profile && !profile.has_shadow_vector) {
    // The redirect is handled at the page level to avoid loops
  }

  return (
    <div className="min-h-screen bg-[#020408]">
      {children}
    </div>
  );
}
