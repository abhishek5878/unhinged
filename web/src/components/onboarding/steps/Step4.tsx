"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const labels: Record<string, string> = {
  "0": "Very rigid",
  "1": "Quite rigid",
  "2": "Somewhat rigid",
  "3": "Slightly rigid",
  "4": "Neutral",
  "5": "Slightly flexible",
  "6": "Fairly adaptable",
  "7": "Quite adaptable",
  "8": "Very adaptable",
  "9": "Extremely fluid",
  "10": "Fully fluid",
};

function getLabel(value: number): string {
  const idx = Math.round(value * 10).toString();
  return labels[idx] || "Moderate";
}

export function Step4() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [value, setValue] = useState(0.5);
  const [touched, setTouched] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  const handleInteraction = useCallback(
    (clientX: number) => {
      if (!trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      setValue(x);
      setTouched(true);

      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setAnswer("entropyTolerance", parseFloat(x.toFixed(2)));
        nextStep();
      }, 1500);
    },
    [setAnswer, nextStep]
  );

  function handlePointerDown(e: React.PointerEvent) {
    e.currentTarget.setPointerCapture(e.pointerId);
    handleInteraction(e.clientX);
  }

  function handlePointerMove(e: React.PointerEvent) {
    if (e.buttons > 0) {
      handleInteraction(e.clientX);
    }
  }

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-16">
        A plan changes completely 2 hours before execution. You feel...
      </h2>

      <div className="px-4">
        <div className="flex justify-between mb-3">
          <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#ff6b35]">
            Like the ground dropped out
          </span>
          <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#00ff9d]">
            Like an adventure started
          </span>
        </div>

        <div
          ref={trackRef}
          className="relative h-3 w-full cursor-pointer rounded-full"
          style={{
            background: "linear-gradient(to right, #ff6b35, #ffd700, #00ff9d)",
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
        >
          <motion.div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-11 w-11 rounded-full bg-white shadow-lg shadow-white/20"
            style={{ left: `${value * 100}%` }}
            animate={{ left: `${value * 100}%` }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          />
        </div>

        {touched && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 text-center font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/60"
          >
            {getLabel(value)}
          </motion.p>
        )}
      </div>
    </div>
  );
}
