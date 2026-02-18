"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { TranscriptEntry } from "@/types/simulation";

interface DialogueTranscriptProps {
  transcript: TranscriptEntry[];
  nameA?: string;
  nameB?: string;
}

export function DialogueTranscript({
  transcript,
  nameA = "You",
  nameB = "Partner",
}: DialogueTranscriptProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript.length]);

  if (transcript.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/20">
          No transcript data
        </p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
      {transcript.map((entry, i) => {
        const isA = entry.role === "agent_a";
        const name = isA ? nameA : nameB;
        const initColor = isA ? "#00c8ff" : "#ff6b35";

        // Check if this looks like a crisis injection (heuristic)
        const isCrisis =
          entry.content.includes("EXTERNAL EVENT") ||
          entry.content.includes("DECISION POINT");

        if (isCrisis) {
          return (
            <div
              key={i}
              className="rounded-lg border border-[#fbbf24]/30 bg-[#fbbf24]/5 p-4"
            >
              <p className="mb-1 font-[family-name:var(--font-space-mono)] text-[10px] font-bold uppercase tracking-wider text-[#fbbf24]">
                External Event
              </p>
              <p className="font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/70 leading-relaxed">
                {entry.content}
              </p>
            </div>
          );
        }

        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${isA ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 ${
                isA ? "bg-[#162638]" : "bg-[#0a1520]"
              }`}
            >
              <div className="mb-1 flex items-center gap-2">
                <span
                  className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
                  style={{ backgroundColor: `${initColor}20`, color: initColor }}
                >
                  {name[0]}
                </span>
                <span className="font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
                  {name}
                </span>
              </div>
              <p className="font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/80 leading-relaxed">
                {entry.content}
              </p>
              <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/20">
                {new Date(entry.timestamp).toLocaleTimeString("en-IN", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
