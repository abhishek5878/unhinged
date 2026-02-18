"use client";

import { motion } from "framer-motion";
import type { MatchCandidate } from "@/types/simulation";

const attachmentColors: Record<string, string> = {
  secure: "#00ff9d",
  anxious: "#00c8ff",
  avoidant: "#ff6b35",
  fearful: "#c084fc",
};

const attachmentLabels: Record<string, string> = {
  secure: "Secure — stable baseline",
  anxious: "Anxious — high signal",
  avoidant: "Avoidant — distance dynamics",
  fearful: "Fearful — push-pull pattern",
};

interface MatchCardProps {
  candidate: MatchCandidate;
  userAttachment?: string;
  onSimulate: () => void;
  onSkip: () => void;
  loading?: boolean;
}

export function MatchCard({
  candidate,
  onSimulate,
  onSkip,
  loading,
}: MatchCardProps) {
  const color = attachmentColors[candidate.attachment_style] || "#e8f4ff";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-[#162638] bg-[#060d14]/50 p-6"
    >
      {/* Name + city */}
      <div className="mb-4">
        <h3 className="font-[family-name:var(--font-syne)] text-xl font-bold text-[#e8f4ff]">
          {candidate.first_name}
        </h3>
        <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
          {candidate.city}
        </p>
      </div>

      {/* Attachment badge */}
      <div
        className="mb-4 inline-block rounded-full px-3 py-1 text-xs font-medium"
        style={{
          backgroundColor: `${color}15`,
          color: color,
          border: `1px solid ${color}30`,
        }}
      >
        <span className="font-[family-name:var(--font-space-mono)]">
          {attachmentLabels[candidate.attachment_style]}
        </span>
      </div>

      {/* Vulnerability hint */}
      <p className="mb-6 font-[family-name:var(--font-crimson-pro)] text-sm italic text-[#e8f4ff]/50 leading-relaxed">
        {candidate.shared_vulnerability_hint}
      </p>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onSimulate}
          disabled={loading}
          className="flex-1 rounded-lg bg-[#00c8ff] px-4 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 hover:shadow-[0_0_20px_#00c8ff30] disabled:opacity-50"
        >
          {loading ? "Starting..." : "Run Simulation"}
        </button>
        <button
          onClick={onSkip}
          className="rounded-lg border border-[#162638] px-4 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#e8f4ff]/50 transition-all hover:border-[#e8f4ff]/20 hover:text-[#e8f4ff]/70"
        >
          Skip
        </button>
      </div>
    </motion.div>
  );
}
