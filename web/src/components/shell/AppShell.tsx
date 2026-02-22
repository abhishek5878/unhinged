"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useClerk, useUser } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  Activity,
  User,
  Settings,
  Menu,
  X,
  LogOut,
} from "lucide-react";

interface AppShellProps {
  profile: {
    email?: string | null;
    name?: string | null;
  };
  children: React.ReactNode;
}

const navItems = [
  { href: "/dashboard", label: "Matches", icon: Users },
  { href: "/dashboard/simulations", label: "Simulations", icon: Activity },
  { href: "/dashboard/profile", label: "Profile", icon: User },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

function SidebarContent({
  profile,
  pathname,
  onClose,
}: {
  profile: AppShellProps["profile"];
  pathname: string;
  onClose?: () => void;
}) {
  const { signOut } = useClerk();
  // useUser() is the authoritative Clerk source — server-side profile.name/email
  // may be empty if /auth/me hasn't been synced yet
  const { user } = useUser();
  const displayName =
    profile.name ||
    user?.fullName ||
    (user?.firstName ? `${user.firstName} ${user.lastName ?? ""}`.trim() : null);
  const displayEmail =
    profile.email ||
    user?.primaryEmailAddress?.emailAddress ||
    null;
  const initial = ((displayName || displayEmail || "U")[0] ?? "U").toUpperCase();

  return (
    <div className="flex h-full flex-col bg-[#060d14] border-r border-[#162638]">
      {/* Logo */}
      <div className="flex items-center justify-between px-6 py-6">
        <Link
          href="/dashboard"
          className="font-[family-name:var(--font-syne)] text-lg font-extrabold text-[#e8f4ff]"
          onClick={onClose}
        >
          PRELUDE
        </Link>
        {onClose && (
          <button onClick={onClose} className="text-[#e8f4ff]/40 md:hidden">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={onClose}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                    isActive
                      ? "border-l-2 border-[#00c8ff] bg-[#00c8ff]/5 text-[#00c8ff] font-medium"
                      : "border-l-2 border-transparent text-[#e8f4ff]/50 hover:bg-[#e8f4ff]/5 hover:text-[#e8f4ff]/80"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="font-[family-name:var(--font-space-mono)]">
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-[#162638] px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#00c8ff]/10 text-[#00c8ff]">
            <span className="font-[family-name:var(--font-syne)] text-xs font-bold">
              {initial}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate font-[family-name:var(--font-space-mono)] text-xs font-semibold text-[#e8f4ff]/80">
              {displayName || displayEmail || "User"}
            </p>
            {displayName && displayEmail && (
              <p className="truncate font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
                {displayEmail}
              </p>
            )}
          </div>
          <button
            onClick={() => signOut()}
            className="text-[#e8f4ff]/30 hover:text-[#e8f4ff]/60 transition-colors"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export function AppShell({ profile, children }: AppShellProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[#020408]">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 md:block">
        <SidebarContent profile={profile} pathname={pathname} />
      </aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -240 }}
              animate={{ x: 0 }}
              exit={{ x: -240 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-50 w-60 md:hidden"
            >
              <SidebarContent
                profile={profile}
                pathname={pathname}
                onClose={() => setMobileOpen(false)}
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Mobile header */}
        <div className="sticky top-0 z-30 flex items-center gap-3 border-b border-[#162638] bg-[#020408]/95 px-4 py-3 backdrop-blur md:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="text-[#e8f4ff]/60"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]">
            PRELUDE
          </span>
        </div>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
