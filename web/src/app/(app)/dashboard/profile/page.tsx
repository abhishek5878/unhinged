"use client";

import { useEffect, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";

interface ProfileData {
  user_id: string;
  has_shadow_vector: boolean;
  onboarding_complete: boolean;
  email: string;
  name: string;
  simulation_count: number;
}

export default function ProfilePage() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const token = await getToken();
        if (!token) return;

        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend"}/auth/me`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          setProfile(await res.json());
        }
      } catch {
        // Backend unreachable
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, [getToken]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-10">
      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          Your Profile
        </p>
        <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          Shadow Vector
        </h1>
      </section>

      <div className="space-y-4">
        {/* Identity */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
            Identity
          </p>
          <div className="mt-4 space-y-3">
            <div className="flex justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                Name
              </span>
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]">
                {user?.fullName || profile?.name || "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                Email
              </span>
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]">
                {user?.primaryEmailAddress?.emailAddress || profile?.email || "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Shadow Vector Status */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
            Shadow Vector
          </p>
          <div className="mt-4 space-y-3">
            <div className="flex justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                Status
              </span>
              <span
                className="font-[family-name:var(--font-space-mono)] text-xs"
                style={{
                  color: profile?.has_shadow_vector ? "#00ff9d" : "#fbbf24",
                }}
              >
                {profile?.has_shadow_vector ? "Complete" : "Incomplete"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                Simulations run
              </span>
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]">
                {profile?.simulation_count ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        {profile?.has_shadow_vector ? (
          <div className="space-y-3">
            <Link
              href={`/profile/${profile.user_id}`}
              className="block w-full rounded-lg border border-[#162638] px-6 py-3 text-center font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/60 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]"
              target="_blank"
            >
              View public card
            </Link>
            <button
              onClick={() => {
                const origin = window.location.origin;
                const text = encodeURIComponent(
                  `I just mapped my relationship blueprint on PRELUDE. Take yours: ${origin}/profile/${profile.user_id}`
                );
                window.open(`https://wa.me/?text=${text}`, "_blank");
              }}
              className="w-full rounded-lg bg-[#25d366] px-6 py-3 font-[family-name:var(--font-space-mono)] text-xs font-bold text-white transition-all hover:bg-[#25d366]/90"
            >
              Share your Shadow Vector on WhatsApp
            </button>
          </div>
        ) : (
          <a
            href="/onboarding"
            className="block w-full rounded-lg bg-[#00c8ff] px-6 py-3 text-center font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90"
          >
            Complete onboarding →
          </a>
        )}
      </div>
    </div>
  );
}
