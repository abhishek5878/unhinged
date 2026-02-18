"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const options = [
  {
    label: "Certainty — I need to know we're okay",
    value: "anxious" as const,
    color: "#00c8ff",
  },
  {
    label: "Space — I need to process alone",
    value: "avoidant" as const,
    color: "#ff6b35",
  },
  {
    label: "Action — I start fixing immediately",
    value: "secure" as const,
    color: "#00ff9d",
  },
  {
    label: "Connection — I want to talk it through",
    value: "fearful" as const,
    color: "#c084fc",
  },
];

export function Step1() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [selected, setSelected] = useState<string | null>(null);

  function handleSelect(value: "secure" | "anxious" | "avoidant" | "fearful") {
    setSelected(value);
    setAnswer("attachmentStyle", value);
    setTimeout(() => nextStep(), 400);
  }

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-12">
        When things fall apart, what do you reach for first?
      </h2>

      <div className="grid grid-cols-2 gap-4">
        {options.map((opt) => (
          <motion.button
            key={opt.value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleSelect(opt.value)}
            className="relative min-h-[120px] rounded-xl border p-5 text-left transition-all duration-200"
            style={{
              borderColor:
                selected === opt.value ? opt.color : "#162638",
              boxShadow:
                selected === opt.value
                  ? `0 0 30px ${opt.color}20`
                  : "none",
              background:
                selected === opt.value ? `${opt.color}08` : "transparent",
            }}
          >
            <span className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/90">
              {opt.label}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
