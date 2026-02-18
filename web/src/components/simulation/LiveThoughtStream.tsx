"use client";

import { motion } from "framer-motion";
import type { BeliefSnapshot } from "@/types/simulation";

const riskColors: Record<string, string> = {
  LOW: "#00ff9d",
  MODERATE: "#fbbf24",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

interface LiveThoughtStreamProps {
  snapshots: BeliefSnapshot[];
  agentLabel?: string;
}

export function LiveThoughtStream({
  snapshots,
  agentLabel = "Agent",
}: LiveThoughtStreamProps) {
  if (snapshots.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/20">
          Awaiting data...
        </p>
      </div>
    );
  }

  // Show last 5 snapshots
  const visible = snapshots.slice(-5);

  return (
    <div className="space-y-3 p-3">
      <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        {agentLabel}&apos;s internal state
      </p>
      {visible.map((snap, i) => {
        const color = riskColors[snap.risk_level] || "#e8f4ff";
        const topSignal = Object.entries(snap.signal_breakdown).sort(
          (a, b) => b[1] - a[1]
        )[0];

        return (
          <motion.div
            key={snap.turn}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-lg bg-[#0a1520] p-3"
            style={{ borderLeft: `3px solid ${color}` }}
          >
            <div className="mb-1 flex items-center justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/30">
                TURN {snap.turn}
              </span>
              <span
                className="rounded-full px-2 py-0.5 font-[family-name:var(--font-space-mono)] text-[9px] font-medium"
                style={{
                  backgroundColor: `${color}15`,
                  color: color,
                }}
              >
                {snap.risk_level}
              </span>
            </div>
            <p className="font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]/80">
              Risk: {(snap.risk * 100).toFixed(0)}%
            </p>
            {topSignal && (
              <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40">
                Top signal: {topSignal[0].replace(/_/g, " ")} (
                {topSignal[1].toFixed(2)})
              </p>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
