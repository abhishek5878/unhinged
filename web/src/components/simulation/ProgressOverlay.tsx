"use client";

import { motion } from "framer-motion";
import type { SimulationProgress } from "@/types/simulation";

interface ProgressOverlayProps {
  progress: SimulationProgress | null;
  onCancel?: () => void;
}

export function ProgressOverlay({ progress, onCancel }: ProgressOverlayProps) {
  const percent = progress?.percent ?? 0;
  const completed = progress?.completed ?? 0;
  const total = progress?.total ?? 100;

  return (
    <div className="flex flex-col items-center justify-center py-20">
      {/* Circular progress */}
      <div className="relative h-40 w-40">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            stroke="#162638"
            strokeWidth="6"
          />
          <motion.circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            stroke="#00c8ff"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 52}
            strokeDashoffset={2 * Math.PI * 52 * (1 - percent / 100)}
            initial={{ strokeDashoffset: 2 * Math.PI * 52 }}
            animate={{
              strokeDashoffset: 2 * Math.PI * 52 * (1 - percent / 100),
            }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-[family-name:var(--font-syne)] text-3xl font-bold text-[#00c8ff]">
            {Math.round(percent)}%
          </span>
        </div>
      </div>

      <p className="mt-6 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/50">
        Simulating timeline{" "}
        <span className="text-[#e8f4ff]">{completed}</span> of{" "}
        <span className="text-[#e8f4ff]">{total}</span>
      </p>

      {/* Scanning animation */}
      <div className="mt-4 h-1 w-48 overflow-hidden rounded-full bg-[#162638]">
        <motion.div
          className="h-full w-12 rounded-full bg-[#00c8ff]/40"
          animate={{ x: ["-48px", "192px"] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <p className="mt-6 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/30">
        Running Monte Carlo simulations across crisis scenarios...
      </p>

      {onCancel && (
        <button
          onClick={onCancel}
          className="mt-8 rounded-lg border border-[#162638] px-6 py-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40 transition-all hover:border-red-500/30 hover:text-red-400"
        >
          Cancel simulation
        </button>
      )}
    </div>
  );
}
