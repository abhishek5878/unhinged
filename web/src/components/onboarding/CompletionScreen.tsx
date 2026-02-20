"use client";

import { useEffect, useState } from "react";
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

export function CompletionScreen() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { answers } = useOnboardingStore();
  const [showContent, setShowContent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const topValues = (answers.valueRanking || []).slice(0, 3);
  const attachment = answers.attachmentStyle || "secure";

  useEffect(() => {
    const timer = setTimeout(() => setShowContent(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  async function handleSubmit() {
    setSubmitting(true);

    try {
      const token = await getToken();
      const API = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

      // Get user profile
      const meRes = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!meRes.ok) throw new Error("Failed to fetch profile");
      const me = await meRes.json();

      // PUT shadow vector
      const shadowVector = transformToShadowVector(answers);
      await fetch(`${API}/profiles/${me.user_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(shadowVector),
      });

      router.push("/dashboard");
    } catch (error) {
      console.error("Submission error:", error);
      setSubmitError("Something went wrong. Please try again.");
      setSubmitting(false);
    }
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
            animate={{
              x: "50vw",
              y: "50vh",
              opacity: 0,
            }}
            transition={{
              duration: 2,
              delay: i * 0.03,
              ease: "easeInOut",
            }}
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

          {/* CTA */}
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 }}
            onClick={handleSubmit}
            disabled={submitting}
            className="mt-12 rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 disabled:opacity-50"
          >
            {submitting ? "Saving..." : "Find my first simulation match →"}
          </motion.button>

          {submitError && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 font-[family-name:var(--font-space-mono)] text-xs text-[#ef4444]"
            >
              {submitError}
            </motion.p>
          )}
        </motion.div>
      )}
    </div>
  );
}
