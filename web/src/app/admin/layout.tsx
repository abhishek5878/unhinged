import { auth, currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();

  if (!userId) {
    redirect("/sign-in");
  }

  const user = await currentUser();
  const role = (user?.publicMetadata as Record<string, unknown>)?.role;

  if (role !== "admin") {
    redirect("/app/dashboard?error=unauthorized");
  }

  return (
    <div className="min-h-screen bg-[#020408]">
      <div className="border-b border-[#162638] p-4">
        <p className="font-mono text-xs text-[#00c8ff] uppercase tracking-widest">
          Admin Dashboard
        </p>
      </div>
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
