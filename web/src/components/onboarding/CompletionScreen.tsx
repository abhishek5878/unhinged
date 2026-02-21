"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { useOnboardingStore, type ShadowVectorAnswers } from "@/lib/onboarding-store";

const attachmentDescriptions: Record<string, string> = {
  anxious:
    "Anxious attachment — You love deeply and need to know it's reciprocated. That's not weakness. That's data.",
  avoidant:
    "Avoidant attachment — You protect your inner world fiercely. Independence isn't a flaw. It's architecture.",
  secure:
    "Secure attachment — You can hold space without losing yourself. That's rare. That's the foundation.",
  fearful:
    "Fearful-avoidant attachment — You want depth but fear what it costs. The tension is the signal, not the noise.",
};

const attachmentLabels: Record<string, string> = {
  anxious: "Anxiously Attached",
  avoidant: "Avoidant",
  secure: "Securely Attached",
  fearful: "Fearful-Avoidant",
};

const valueLabels: Record<string, string> = {
  autonomy: "Freedom",
  security: "Security",
  achievement: "Achievement",
  intimacy: "Depth",
  novelty: "Adventure",
  stability: "Stability",
  power: "Influence",
  belonging: "Belonging",
};

function transformToShadowVector(answers: Partial<ShadowVectorAnswers>) {
  const ranking = answers.valueRanking || [];
  const values: Record<string, number> = {};
  ranking.forEach((key, i) => {
    values[key] = parseFloat((1.0 - i * 0.08).toFixed(2));
  });

  return {
    values,
    attachment_style: answers.attachmentStyle || "secure",
    fear_architecture: answers.fearArchitecture || [],
    linguistic_signature: answers.linguisticSignature || [],
    entropy_tolerance: answers.entropyTolerance ?? 0.5,
    communication_style:
      (answers.communicationStyle?.directness ?? 0.5) >= 0.5
        ? "direct"
        : "indirect",
  };
}

type SaveState = "saving" | "saved" | "error";

export function CompletionScreen() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { answers } = useOnboardingStore();
  const [showContent, setShowContent] = useState(false);
  const [saveState, setSaveState] = useState<SaveState>("saving");
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [copyDone, setCopyDone] = useState(false);
  const [showInvite, setShowInvite] = useState(false);

  const topValues = (answers.valueRanking || []).slice(0, 3);
  const attachment = answers.attachmentStyle || "secure";
  const attachmentLabel = attachmentLabels[attachment] || "Securely Attached";

  // ── 1. Reveal content after particle animation ──────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => setShowContent(true), 1800);
    return () => clearTimeout(timer);
  }, []);

  // ── 2. Auto-save shadow vector immediately on mount ─────────────────────────
  const autoSave = useCallback(async () => {
    setSaveState("saving");
    try {
      const token = await getToken();
      const API = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

      const meRes = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!meRes.ok) throw new Error("profile fetch failed");
      const me = await meRes.json();

      const shadowVector = transformToShadowVector(answers);
      const putRes = await fetch(`${API}/profiles/${me.user_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(shadowVector),
      });
      if (!putRes.ok) throw new Error("profile save failed");

      // Generate invite token
      try {
        const inviteRes = await fetch(`${API}/invites`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (inviteRes.ok) {
          const inv = await inviteRes.json();
          const origin =
            typeof window !== "undefined" ? window.location.origin : "https://prelude.app";
          setInviteLink(`${origin}/simulate/invite/${inv.token}`);
        }
      } catch {
        // invite generation failing is non-fatal
      }

      setSaveState("saved");
    } catch {
      setSaveState("error");
    }
  }, [answers, getToken]);

  useEffect(() => {
    autoSave();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 3. Copy invite link ─────────────────────────────────────────────────────
  async function handleCopyLink() {
    if (!inviteLink) return;
    await navigator.clipboard.writeText(inviteLink);
    setCopyDone(true);
    setTimeout(() => setCopyDone(false), 2000);
  }

  // ── 4. WhatsApp share ───────────────────────────────────────────────────────
  function handleWhatsApp() {
    const link = inviteLink ?? (typeof window !== "undefined" ? window.location.origin + "/match" : "https://prelude.app/match");
    const text = encodeURIComponent(
      `I just found out I'm ${attachmentLabel} on PRELUDE. Take yours and tell me if we'd have survived month 3 together: ${link}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  }

  // ── 5. Navigate to dashboard ────────────────────────────────────────────────
  function handleContinue() {
    router.push("/dashboard");
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#020408] overflow-hidden">
      {/* Particle effect */}
      <div className="absolute inset-0 pointer-events-none">
        {Array.from({ length: 40 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute h-1 w-1 rounded-full bg-[#00c8ff]"
            initial={{
              x: Math.random() * (typeof window !== "undefined" ? window.innerWidth : 400),
              y: Math.random() * (typeof window !== "undefined" ? window.innerHeight : 800),
              opacity: 0.3,
            }}
            animate={{ x: "50vw", y: "50vh", opacity: 0 }}
            transition={{ duration: 2, delay: i * 0.03, ease: "easeInOut" }}
          />
        ))}
      </div>

      {showContent && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 w-full max-w-md px-4 text-center"
        >
          {/* Saving indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-6 flex items-center justify-center gap-2"
          >
            {saveState === "saving" && (
              <>
                <div className="h-3 w-3 animate-spin rounded-full border border-[#00c8ff]/40 border-t-[#00c8ff]" />
                <span className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-[0.2em] text-[#e8f4ff]/30">
                  Saving profile…
                </span>
              </>
            )}
            {saveState === "saved" && (
              <span className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-[0.2em] text-[#00c8ff]/60">
                ✓ Profile saved
              </span>
            )}
            {saveState === "error" && (
              <span className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-[0.2em] text-[#fbbf24]/60">
                Saved locally — will sync on dashboard
              </span>
            )}
          </motion.div>

          {/* Top 3 values */}
          <div className="space-y-2 mb-10">
            {topValues.map((v, i) => (
              <motion.p
                key={v}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.15 }}
                className="font-[family-name:var(--font-syne)] font-extrabold text-[#e8f4ff]"
                style={{ fontSize: `${32 - i * 4}px` }}
              >
                {valueLabels[v] || v}
              </motion.p>
            ))}
          </div>

          {/* Attachment style */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/70 leading-relaxed max-w-sm mx-auto"
          >
            {attachmentDescriptions[attachment]}
          </motion.p>

          {/* Invite toggle */}
          {!showInvite ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
              className="mt-12 space-y-3"
            >
              <button
                onClick={() => setShowInvite(true)}
                disabled={saveState === "saving"}
                className="w-full rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 hover:shadow-[0_0_30px_#00c8ff30] disabled:opacity-40"
              >
                Invite someone to simulate →
              </button>
              <button
                onClick={handleContinue}
                className="w-full rounded-lg border border-[#162638] px-8 py-3 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]/80"
              >
                Go to dashboard
              </button>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-12 rounded-xl border border-[#162638] bg-[#060d14]/60 p-6 text-left space-y-4"
            >
              <p className="font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]">
                Run your first simulation
              </p>
              <p className="font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
                Invite someone you&apos;re already curious about. They complete
                their profile, then PRELUDE simulates 100+ futures of your
                relationship.
              </p>

              {inviteLink ? (
                <>
                  <div className="rounded-lg border border-[#162638] bg-[#020408] px-3 py-2.5">
                    <p className="font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40 truncate">
                      {inviteLink}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleCopyLink}
                      className="flex-1 rounded-lg border border-[#162638] px-4 py-2.5 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/60 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]"
                    >
                      {copyDone ? "✓ Copied" : "Copy link"}
                    </button>
                    <button
                      onClick={handleWhatsApp}
                      className="flex-1 rounded-lg bg-[#25d366] px-4 py-2.5 font-[family-name:var(--font-space-mono)] text-xs font-bold text-white transition-all hover:bg-[#25d366]/90"
                    >
                      WhatsApp
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2 py-2">
                  <div className="h-3 w-3 animate-spin rounded-full border border-[#00c8ff]/40 border-t-[#00c8ff]" />
                  <span className="font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
                    Generating link…
                  </span>
                </div>
              )}

              <button
                onClick={handleContinue}
                className="w-full rounded-lg border border-[#162638] px-8 py-2.5 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40 transition-colors hover:text-[#e8f4ff]/70"
              >
                Skip — go to dashboard
              </button>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
}
