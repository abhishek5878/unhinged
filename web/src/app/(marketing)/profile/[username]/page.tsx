"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";

const attachmentLabels: Record<string, string> = {
  anxious: "Anxiously Attached",
  avoidant: "Avoidant",
  secure: "Securely Attached",
  fearful: "Fearful-Avoidant",
};

const attachmentReads: Record<string, string> = {
  anxious: "You love deeply and need to know it's reciprocated. That's not weakness. That's data.",
  avoidant: "You protect your inner world fiercely. Independence isn't a flaw. It's architecture.",
  secure: "You can hold space without losing yourself. That's rare. That's the foundation.",
  fearful: "You want depth but fear what it costs. The tension is the signal, not the noise.",
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

interface ProfileData {
  attachment_style: string;
  top_values: string[];
}

export default function PublicProfilePage() {
  const params = useParams();
  // username is the user's UUID (profile id)
  const userId = params.username as string;

  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  const API = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API}/profiles/${userId}`);
        if (!res.ok) throw new Error("not found");
        const data = await res.json();
        const sv = data.shadow_vector ?? {};
        const valueMap: Record<string, number> = sv.values ?? {};
        const topValues = Object.entries(valueMap)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([k]) => k);
        setProfile({
          attachment_style: sv.attachment_style ?? "secure",
          top_values: topValues,
        });
      } catch {
        setProfile(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [userId, API]);

  const cardUrl = `${typeof window !== "undefined" ? window.location.origin : ""}/api/shadow-vector/card/${userId}`;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#020408]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#020408] px-4 text-center">
        <p className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          Profile not found.
        </p>
        <Link href="/match" className="font-[family-name:var(--font-space-mono)] text-sm text-[#00c8ff]">
          Discover PRELUDE →
        </Link>
      </div>
    );
  }

  const label = attachmentLabels[profile.attachment_style] ?? "Profiled";
  const read = attachmentReads[profile.attachment_style] ?? "";

  function handleDownload() {
    const link = document.createElement("a");
    link.href = `${cardUrl}?format=square`;
    link.download = `prelude-shadow-vector.png`;
    link.click();
  }

  function handleWhatsApp() {
    const origin = typeof window !== "undefined" ? window.location.origin : "https://tryprior.xyz";
    const text = encodeURIComponent(
      `I'm ${label} on PRELUDE. Take yours and tell me if we'd survive: ${origin}/profile/${userId}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  }

  return (
    <div className="min-h-screen bg-[#020408] px-4 py-16">
      <div className="mx-auto max-w-lg">
        {/* Card preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-[#162638] bg-[#060d14] p-10 text-center"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 20% 30%, rgba(0,200,255,0.04) 0%, transparent 70%), #060d14",
          }}
        >
          {/* PRELUDE badge */}
          <div className="mb-8 inline-block rounded-full border border-[#00c8ff]/30 px-4 py-1.5">
            <span className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-[0.25em] text-[#00c8ff]/70">
              PRELUDE · SHADOW VECTOR
            </span>
          </div>

          {/* Values */}
          <div className="mb-8 space-y-1">
            {profile.top_values.map((v, i) => (
              <p
                key={v}
                className="font-[family-name:var(--font-syne)] font-extrabold text-[#e8f4ff]"
                style={{ fontSize: `${36 - i * 6}px`, opacity: 1 - i * 0.15 }}
              >
                {valueLabels[v] ?? v}
              </p>
            ))}
          </div>

          {/* Divider */}
          <div className="mx-auto mb-6 h-px w-12 bg-[#00c8ff]/40" />

          {/* Attachment */}
          <p className="font-[family-name:var(--font-space-mono)] text-sm font-semibold text-[#00c8ff]">
            {label}
          </p>
          <p className="mx-auto mt-2 max-w-xs font-[family-name:var(--font-crimson-pro)] text-base text-[#e8f4ff]/50 leading-relaxed">
            {read}
          </p>
        </motion.div>

        {/* Share actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 space-y-3"
        >
          <button
            onClick={handleDownload}
            className="w-full rounded-lg border border-[#162638] px-6 py-3 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/60 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]"
          >
            Download PNG
          </button>
          <button
            onClick={handleWhatsApp}
            className="w-full rounded-lg bg-[#25d366] px-6 py-3 font-[family-name:var(--font-space-mono)] text-sm font-bold text-white transition-all hover:bg-[#25d366]/90"
          >
            Share on WhatsApp
          </button>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-10 rounded-xl border border-[#162638] bg-[#060d14]/60 p-6 text-center"
        >
          <p className="font-[family-name:var(--font-syne)] text-base font-bold text-[#e8f4ff]">
            What&apos;s your Shadow Vector?
          </p>
          <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/40">
            Take the 3-minute profile. Then simulate a future together.
          </p>
          <Link
            href="/match"
            className="mt-4 inline-block rounded-lg bg-[#00c8ff] px-6 py-3 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90"
          >
            Build yours on PRELUDE →
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
