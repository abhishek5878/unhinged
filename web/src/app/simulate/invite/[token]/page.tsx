"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, useUser } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { getInviteInfo, claimInvite } from "@/lib/api";

const INVITE_TOKEN_KEY = "prelude_pending_invite";

const attachmentLabels: Record<string, string> = {
  anxious: "Anxiously Attached",
  avoidant: "Avoidant",
  secure: "Securely Attached",
  fearful: "Fearful-Avoidant",
  unknown: "Profiled",
};

type InviteStatus = "loading" | "valid" | "claimed" | "expired" | "not_found";

export default function InvitePage() {
  const params = useParams();
  const router = useRouter();
  const { getToken, isLoaded: authLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  const inviteToken = params.token as string;

  const [status, setStatus] = useState<InviteStatus>("loading");
  const [inviterStyle, setInviterStyle] = useState("unknown");
  const [claiming, setClaiming] = useState(false);
  const [claimError, setClaimError] = useState<string | null>(null);

  const userId = (user?.publicMetadata as { user_id?: string })?.user_id;
  const hasShadowVector = user?.publicMetadata
    ? Boolean((user.publicMetadata as { has_shadow_vector?: boolean }).has_shadow_vector)
    : false;

  // ── Fetch invite info ──────────────────────────────────────────────────────
  useEffect(() => {
    async function load() {
      try {
        const info = await getInviteInfo(inviteToken);
        if (info.status === "claimed") {
          setStatus("claimed");
        } else if (info.status === "expired") {
          setStatus("expired");
        } else {
          setStatus("valid");
          setInviterStyle(info.inviter_attachment_style);
        }
      } catch {
        setStatus("not_found");
      }
    }
    load();
  }, [inviteToken]);

  // ── Store token in localStorage so post-onboarding flow can claim it ───────
  useEffect(() => {
    if (status === "valid") {
      if (typeof window !== "undefined") {
        localStorage.setItem(INVITE_TOKEN_KEY, inviteToken);
      }
    }
  }, [status, inviteToken]);

  // ── Claim invite ───────────────────────────────────────────────────────────
  async function handleClaim() {
    if (!isSignedIn) return;
    setClaiming(true);
    setClaimError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      const result = await claimInvite(token, inviteToken);
      if (typeof window !== "undefined") {
        localStorage.removeItem(INVITE_TOKEN_KEY);
      }
      router.push(`/dashboard/simulation/${result.simulation_id}`);
    } catch (err) {
      setClaimError(err instanceof Error ? err.message : "Something went wrong");
      setClaiming(false);
    }
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (status === "loading" || !authLoaded) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#020408]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  // ── Invalid / expired ──────────────────────────────────────────────────────
  if (status === "not_found" || status === "expired" || status === "claimed") {
    const msgs = {
      not_found: { title: "Invite not found.", sub: "This link may be invalid." },
      expired: { title: "This invite has expired.", sub: "Invite links are valid for 72 hours." },
      claimed: { title: "This invite has already been used.", sub: "Each invite can only be accepted once." },
    };
    const msg = msgs[status];
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#020408] px-4 text-center">
        <p className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          {msg.title}
        </p>
        <p className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/40">
          {msg.sub}
        </p>
        <Link
          href="/match"
          className="mt-4 rounded-lg bg-[#00c8ff] px-6 py-3 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408]"
        >
          Join PRELUDE →
        </Link>
      </div>
    );
  }

  // ── Valid invite — not signed in ───────────────────────────────────────────
  if (!isSignedIn) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#020408] px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md text-center"
        >
          <div className="mb-6 inline-block rounded-full border border-[#162638] bg-[#060d14]/80 px-4 py-1.5">
            <span className="font-[family-name:var(--font-space-mono)] text-[11px] uppercase tracking-[0.25em] text-[#00c8ff]/80">
              PRELUDE
            </span>
          </div>

          <h1 className="font-[family-name:var(--font-syne)] text-3xl font-extrabold text-[#e8f4ff]">
            Someone {attachmentLabels[inviterStyle] || "profiled"} wants to
            simulate a future with you.
          </h1>

          <p className="mx-auto mt-4 max-w-sm font-[family-name:var(--font-crimson-pro)] text-lg text-[#e8f4ff]/50 leading-relaxed">
            PRELUDE runs 100+ timelines of your relationship — the fights, the
            growth, the breaking points. See what you&apos;d actually build
            together.
          </p>

          <div className="mt-10 space-y-3">
            <Link
              href={`/sign-up?redirect_url=/simulate/invite/${inviteToken}`}
              className="block w-full rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90"
            >
              Create your profile + run the simulation →
            </Link>
            <Link
              href={`/sign-in?redirect_url=/simulate/invite/${inviteToken}`}
              className="block w-full rounded-lg border border-[#162638] px-8 py-3 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]/80"
            >
              Sign in
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  // ── Valid invite — signed in but no shadow vector ─────────────────────────
  if (!userId || !hasShadowVector) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#020408] px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md text-center"
        >
          <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
            Complete your profile first.
          </h1>
          <p className="mx-auto mt-4 max-w-sm font-[family-name:var(--font-crimson-pro)] text-lg text-[#e8f4ff]/50 leading-relaxed">
            Your invite will be waiting when you finish your Shadow Vector (3
            minutes).
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-block rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408]"
          >
            Build my Shadow Vector →
          </Link>
        </motion.div>
      </div>
    );
  }

  // ── Valid invite — ready to claim ─────────────────────────────────────────
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#020408] px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md text-center"
      >
        <div className="mb-6 inline-block rounded-full border border-[#162638] bg-[#060d14]/80 px-4 py-1.5">
          <span className="font-[family-name:var(--font-space-mono)] text-[11px] uppercase tracking-[0.25em] text-[#00c8ff]/80">
            PRELUDE
          </span>
        </div>

        <h1 className="font-[family-name:var(--font-syne)] text-3xl font-extrabold text-[#e8f4ff]">
          Ready to simulate.
        </h1>

        <p className="mx-auto mt-4 max-w-sm font-[family-name:var(--font-crimson-pro)] text-lg text-[#e8f4ff]/50 leading-relaxed">
          Someone{" "}
          <span className="text-[#00c8ff]">
            {attachmentLabels[inviterStyle] || "profiled"}
          </span>{" "}
          invited you. PRELUDE will run 20 timelines of what your relationship
          might look like.
        </p>

        <button
          onClick={handleClaim}
          disabled={claiming}
          className="mt-10 w-full rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 hover:shadow-[0_0_30px_#00c8ff30] disabled:opacity-50"
        >
          {claiming ? "Starting simulation…" : "Run the simulation →"}
        </button>

        {claimError && (
          <p className="mt-4 font-[family-name:var(--font-space-mono)] text-xs text-[#ef4444]">
            {claimError}
          </p>
        )}
      </motion.div>
    </div>
  );
}
