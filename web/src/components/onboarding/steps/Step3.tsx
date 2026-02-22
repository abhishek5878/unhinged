"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const fears = [
  { id: "abandonment", label: "Being left behind" },
  { id: "engulfment", label: "Being trapped" },
  { id: "failure", label: "Failing publicly" },
  { id: "loss_of_identity", label: "Losing yourself" },
  { id: "misunderstood", label: "Being misunderstood" },
  { id: "irrelevance", label: "Becoming irrelevant" },
  { id: "inadequacy", label: "Not being enough" },
  { id: "loss_of_control", label: "Losing control" },
];

export function Step3() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>([]);

  function toggle(id: string) {
    // Side effects must NOT live inside a functional updater — React may call
    // updaters more than once (Strict Mode / concurrent rendering), which would
    // set duplicate timers and call nextStep() twice, skipping a step.
    if (selected.includes(id)) {
      setSelected(selected.filter((f) => f !== id));
      return;
    }
    if (selected.length >= 4) return;
    const next = [...selected, id];
    setSelected(next);
    if (next.length === 4) {
      setAnswer("fearArchitecture", next);
      setTimeout(() => nextStep(), 400);
    }
  }

  function handleContinue() {
    if (selected.length >= 2) {
      setAnswer("fearArchitecture", selected);
      nextStep();
    }
  }

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-12">
        Which of these keeps you up at night? Pick 2 to 4.
      </h2>

      <div className="flex flex-wrap justify-center gap-3">
        {fears.map((fear) => {
          const isSelected = selected.includes(fear.id);
          return (
            <motion.button
              key={fear.id}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => toggle(fear.id)}
              className="rounded-full border px-5 py-2.5 font-[family-name:var(--font-space-mono)] text-sm transition-all duration-200"
              style={{
                borderColor: isSelected ? "#00c8ff" : "#162638",
                background: isSelected ? "#00c8ff15" : "transparent",
                color: isSelected ? "#00c8ff" : "#e8f4ff",
                boxShadow: isSelected ? "0 0 20px #00c8ff15" : "none",
              }}
            >
              {fear.label}
            </motion.button>
          );
        })}
      </div>

      {selected.length >= 2 && selected.length < 4 && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={handleContinue}
          className="mx-auto mt-10 block rounded-lg bg-[#00c8ff] px-8 py-3 text-sm font-semibold text-[#020408] transition-colors hover:bg-[#00c8ff]/90"
        >
          Continue
        </motion.button>
      )}
    </div>
  );
}
