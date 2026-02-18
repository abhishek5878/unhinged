"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";

const quadrants = [
  { label: "The Processor", x: "left", y: "top" },
  { label: "The Challenger", x: "right", y: "top" },
  { label: "The Diplomat", x: "left", y: "bottom" },
  { label: "The Expresser", x: "right", y: "bottom" },
];

function getStyleLabel(x: number, y: number): string {
  if (x < 0.5 && y < 0.5) return "The Processor — indirect and reserved";
  if (x >= 0.5 && y < 0.5) return "The Challenger — direct and reserved";
  if (x < 0.5 && y >= 0.5) return "The Diplomat — indirect and expressive";
  return "The Expresser — direct and expressive";
}

export function Step6() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleInteraction = useCallback(
    (clientX: number, clientY: number) => {
      if (!gridRef.current) return;
      const rect = gridRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const y = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));
      setPos({ x, y });

      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setAnswer("communicationStyle", {
          directness: parseFloat(x.toFixed(2)),
          expressiveness: parseFloat(y.toFixed(2)),
        });
        nextStep();
      }, 1000);
    },
    [setAnswer, nextStep]
  );

  return (
    <div className="w-full max-w-lg">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-10">
        Where do you actually sit?
      </h2>

      <div className="mx-auto max-w-[400px]">
        {/* Axis labels */}
        <div className="flex justify-between mb-2">
          <span className="font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40">
            Indirect
          </span>
          <span className="font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40">
            Direct
          </span>
        </div>

        <div className="relative flex">
          <span className="absolute -left-6 top-0 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40 writing-mode-vertical rotate-180"
            style={{ writingMode: "vertical-lr", transform: "rotate(180deg)" }}
          >
            Reserved
          </span>

          <div
            ref={gridRef}
            className="relative aspect-square w-full cursor-crosshair rounded-xl border border-[#162638] bg-[#0a1020]"
            onPointerDown={(e) => {
              e.currentTarget.setPointerCapture(e.pointerId);
              handleInteraction(e.clientX, e.clientY);
            }}
            onPointerMove={(e) => {
              if (e.buttons > 0) handleInteraction(e.clientX, e.clientY);
            }}
          >
            {/* Grid lines */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#162638]" />
            <div className="absolute top-1/2 left-0 right-0 h-px bg-[#162638]" />

            {/* Quadrant labels */}
            {quadrants.map((q) => (
              <span
                key={q.label}
                className="absolute font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/20"
                style={{
                  [q.x]: "12px",
                  [q.y]: "12px",
                }}
              >
                {q.label}
              </span>
            ))}

            {/* Dot */}
            {pos && (
              <motion.div
                className="absolute h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#00c8ff] shadow-lg"
                style={{
                  left: `${pos.x * 100}%`,
                  top: `${pos.y * 100}%`,
                  boxShadow: "0 0 20px #00c8ff60",
                }}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
              />
            )}
          </div>

          <span className="absolute -right-6 bottom-0 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/40"
            style={{ writingMode: "vertical-lr" }}
          >
            Expressive
          </span>
        </div>

        {pos && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 text-center font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/60"
          >
            {getStyleLabel(pos.x, pos.y)}
          </motion.p>
        )}
      </div>
    </div>
  );
}
