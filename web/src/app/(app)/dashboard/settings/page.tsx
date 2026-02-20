"use client";

import { useClerk } from "@clerk/nextjs";

export default function SettingsPage() {
  const { signOut } = useClerk();

  return (
    <div className="mx-auto max-w-2xl space-y-10">
      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          Preferences
        </p>
        <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          Settings
        </h1>
      </section>

      <div className="space-y-4">
        {/* Account */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
            Account
          </p>
          <div className="mt-4 space-y-4">
            <button
              onClick={() => signOut()}
              className="rounded-lg border border-[#162638] px-5 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#e8f4ff]/50 transition-all hover:border-[#ef4444]/30 hover:text-[#ef4444]"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Data */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
            Data & Privacy
          </p>
          <div className="mt-4">
            <button
              disabled
              className="rounded-lg border border-[#162638] px-5 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#e8f4ff]/30 transition-all"
              title="Coming soon"
            >
              Export my data
            </button>
            <p className="mt-2 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/20">
              Download all your profile and simulation data. Coming soon.
            </p>
          </div>
        </div>

        {/* Danger zone */}
        <div className="rounded-xl border border-[#ef4444]/20 p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#ef4444]/50">
            Danger Zone
          </p>
          <div className="mt-4">
            <button
              disabled
              className="rounded-lg border border-[#ef4444]/30 px-5 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#ef4444]/50 transition-all"
              title="Coming soon"
            >
              Delete my account
            </button>
            <p className="mt-2 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/20">
              Permanently delete your account and all associated data. This
              action cannot be undone.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
