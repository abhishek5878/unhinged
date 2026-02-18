"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { checkWaitlist } from "@/lib/api";

function WaitlistReferralContent() {
  const searchParams = useSearchParams();
  const code = searchParams.get("code");
  const email = searchParams.get("email");

  const [position, setPosition] = useState<number | null>(null);
  const [referralCode, setReferralCode] = useState(code || "");
  const [referralCount, setReferralCount] = useState(0);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(!!email);

  const referralLink = typeof window !== "undefined"
    ? `${window.location.origin}/match?ref=${referralCode}`
    : "";

  useEffect(() => {
    if (email) {
      checkWaitlist(email)
        .then((data) => {
          if (data.on_waitlist) {
            setPosition(data.position);
            setReferralCode(data.referral_code || "");
            setReferralCount(data.referral_count);
          }
        })
        .finally(() => setLoading(false));
    }
  }, [email]);

  function handleCopy() {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleShareWhatsApp() {
    const text = `I just joined the APRIORI MATCH waitlist — they simulate 100+ futures of your relationship before you commit. Join using my link: ${referralLink}`;
    window.open(
      `https://wa.me/?text=${encodeURIComponent(text)}`,
      "_blank"
    );
  }

  function handleShareTwitter() {
    const text = `Just joined @apriori_match — they use AI to simulate 100+ relationship timelines before you commit. Wild. ${referralLink}`;
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
      "_blank"
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#020408]">
        <p className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/40">
          Loading...
        </p>
      </div>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#020408] px-4">
      <div className="w-full max-w-md text-center">
        {/* Position */}
        {position && (
          <div className="mb-10">
            <p className="font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
              Your position
            </p>
            <p className="mt-2 font-[family-name:var(--font-syne)] text-6xl font-extrabold text-[#00c8ff]">
              #{position}
            </p>
          </div>
        )}

        {/* Referral stats */}
        <div className="rounded-xl border border-[#162638] p-8">
          <p className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff]">
            Move up the waitlist
          </p>
          <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-[#e8f4ff]/50">
            Each referral moves you closer to early access.
          </p>

          {/* Referral count */}
          <div className="mt-6 rounded-lg border border-[#162638] p-4">
            <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
              Referrals
            </p>
            <p className="mt-1 font-[family-name:var(--font-syne)] text-3xl font-bold text-[#ff6b35]">
              {referralCount}
            </p>
            {/* Progress bar */}
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[#162638]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#ff6b35] to-[#00c8ff] transition-all"
                style={{ width: `${Math.min(referralCount * 20, 100)}%` }}
              />
            </div>
            <p className="mt-2 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
              {referralCount}/5 for priority access
            </p>
          </div>

          {/* Referral link */}
          <div className="mt-6">
            <p className="mb-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
              Your referral link
            </p>
            <div className="flex items-center gap-2 rounded-lg border border-[#162638] bg-[#020408] p-3">
              <input
                readOnly
                value={referralLink}
                className="flex-1 bg-transparent font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/60 outline-none"
              />
              <button
                onClick={handleCopy}
                className="shrink-0 rounded-md bg-[#162638] px-3 py-1.5 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/70 transition-all hover:bg-[#1e3550]"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

          {/* Share buttons */}
          <div className="mt-6 flex gap-3">
            <button
              onClick={handleShareWhatsApp}
              className="flex-1 rounded-lg bg-[#25D366]/10 py-3 font-[family-name:var(--font-syne)] text-sm font-bold text-[#25D366] transition-all hover:bg-[#25D366]/20"
            >
              WhatsApp
            </button>
            <button
              onClick={handleShareTwitter}
              className="flex-1 rounded-lg bg-[#1DA1F2]/10 py-3 font-[family-name:var(--font-syne)] text-sm font-bold text-[#1DA1F2] transition-all hover:bg-[#1DA1F2]/20"
            >
              Twitter
            </button>
            <button
              onClick={handleCopy}
              className="flex-1 rounded-lg bg-[#162638] py-3 font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]/70 transition-all hover:bg-[#1e3550]"
            >
              {copied ? "Copied!" : "Copy link"}
            </button>
          </div>
        </div>

        {/* Back link */}
        <a
          href="/match"
          className="mt-8 inline-block font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30 hover:text-[#e8f4ff]/50 transition-colors"
        >
          ← Back to APRIORI MATCH
        </a>
      </div>
    </main>
  );
}

export default function WaitlistReferralPage() {
  return (
    <Suspense fallback={null}>
      <WaitlistReferralContent />
    </Suspense>
  );
}
