"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const options = [
  { value: "never", label: "Never had one" },
  { value: "under_1y", label: "Under a year" },
  { value: "1_3y", label: "1–3 years" },
  { value: "3y_plus", label: "3+ years" },
];

export function Step8() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [selected, setSelected] = useState<string | null>(null);

  function handleSelect(value: string) {
    setSelected(value);
    setAnswer("relationshipHistory", value);
    setTimeout(() => nextStep(), 400);
  }

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-12">
        Your last serious relationship lasted...
      </h2>

      <div className="grid grid-cols-2 gap-4">
        {options.map((opt) => (
          <motion.button
            key={opt.value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleSelect(opt.value)}
            className="min-h-[100px] rounded-xl border p-5 font-[family-name:var(--font-space-mono)] text-sm transition-all duration-200"
            style={{
              borderColor: selected === opt.value ? "#00c8ff" : "#162638",
              background:
                selected === opt.value ? "#00c8ff08" : "transparent",
              color: selected === opt.value ? "#00c8ff" : "#e8f4ff",
              boxShadow:
                selected === opt.value
                  ? "0 0 30px #00c8ff15"
                  : "none",
            }}
          >
            {opt.label}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
