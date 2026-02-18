"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const options = [
  { value: 0.0, label: "I'm a complete mystery" },
  { value: 0.25, label: "Mostly hidden" },
  { value: 0.5, label: "50/50" },
  { value: 0.75, label: "Fairly readable" },
  { value: 1.0, label: "Open book" },
];

export function Step7() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [selected, setSelected] = useState<number | null>(null);

  function handleSelect(value: number) {
    setSelected(value);
    setAnswer("selfTransparency", value);
    setTimeout(() => nextStep(), 400);
  }

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-12">
        How well do people actually understand your inner world?
      </h2>

      <div className="flex flex-wrap justify-center gap-3">
        {options.map((opt) => (
          <motion.button
            key={opt.value}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => handleSelect(opt.value)}
            className="rounded-full border px-5 py-3 font-[family-name:var(--font-space-mono)] text-sm transition-all duration-200"
            style={{
              borderColor: selected === opt.value ? "#00c8ff" : "#162638",
              background:
                selected === opt.value ? "#00c8ff15" : "transparent",
              color: selected === opt.value ? "#00c8ff" : "#e8f4ff",
              boxShadow:
                selected === opt.value ? "0 0 20px #00c8ff15" : "none",
            }}
          >
            {opt.label}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
