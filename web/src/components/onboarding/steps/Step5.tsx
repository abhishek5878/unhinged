"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const bubbles = [
  {
    id: "a",
    text: "yaar sorted scene hai, don't stress — it's a vibe, trust the process",
    phrases: ["sorted scene", "it's a vibe", "trust the process"],
    time: "10:42 PM",
  },
  {
    id: "b",
    text: "bhai pakka sorted. plan A fail hua toh plan B hai, bindaas",
    phrases: ["pakka", "bindaas", "plan B hai"],
    time: "10:43 PM",
  },
  {
    id: "c",
    text: "i think we should talk this through properly, I'm feeling a bit off",
    phrases: ["talk this through", "feeling a bit off"],
    time: "10:44 PM",
  },
  {
    id: "d",
    text: "full filmy moment ngl 😭 but we'll figure it out, we always do",
    phrases: ["full filmy", "we always do"],
    time: "10:45 PM",
  },
  {
    id: "e",
    text: "ok so i've been thinking and honestly i need some space to process",
    phrases: ["need some space", "been thinking"],
    time: "10:46 PM",
  },
  {
    id: "f",
    text: "chalte hai. whatever happens, happens. overthinking is overrated",
    phrases: ["chalte hai", "overthinking is overrated"],
    time: "10:47 PM",
  },
];

export function Step5() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>([]);

  function toggle(id: string) {
    // Side effects must NOT live inside a functional updater — React may call
    // updaters more than once, which would schedule duplicate timers.
    if (selected.includes(id)) {
      setSelected(selected.filter((b) => b !== id));
      return;
    }
    if (selected.length >= 2) return;
    const next = [...selected, id];
    setSelected(next);
    if (next.length === 2) {
      const phrases = bubbles
        .filter((b) => next.includes(b.id))
        .flatMap((b) => b.phrases);
      setAnswer("linguisticSignature", phrases);
      setTimeout(() => nextStep(), 400);
    }
  }

  return (
    <div className="w-full max-w-md">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-10">
        Which of these could you have sent? Pick your two.
      </h2>

      <div className="space-y-3">
        {bubbles.map((bubble) => {
          const isSelected = selected.includes(bubble.id);
          return (
            <motion.button
              key={bubble.id}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggle(bubble.id)}
              className="w-full text-left rounded-xl p-4 transition-all duration-200"
              style={{
                background: isSelected ? "#075e54" : "#1a2e35",
                border: isSelected
                  ? "1px solid #00c8ff"
                  : "1px solid transparent",
                boxShadow: isSelected ? "0 0 20px #00c8ff10" : "none",
              }}
            >
              <p className="text-sm text-[#e8f4ff]/90 leading-relaxed">
                {bubble.text}
              </p>
              <p className="mt-1 text-right font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40">
                {bubble.time}
              </p>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
