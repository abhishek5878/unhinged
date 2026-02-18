"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ProgressOverlay } from "./ProgressOverlay";
import { DialogueTranscript } from "./DialogueTranscript";
import { LiveThoughtStream } from "./LiveThoughtStream";
import { CollapseRiskMeter } from "./CollapseRiskMeter";
import { TimelineSelector } from "./TimelineSelector";
import type { SimulationResults, SimulationProgress } from "@/types/simulation";

type Tab = "thoughts_a" | "dialogue" | "risk";

interface SimulationViewerProps {
  status: "connecting" | "running" | "completed" | "failed" | "idle";
  progress: SimulationProgress | null;
  results: SimulationResults | null;
  onCancel?: () => void;
}

export function SimulationViewer({
  status,
  progress,
  results,
  onCancel,
}: SimulationViewerProps) {
  const [selectedTimeline, setSelectedTimeline] = useState(0);
  const [mobileTab, setMobileTab] = useState<Tab>("dialogue");

  const isRunning = status === "running" || status === "connecting";
  const timeline = results?.timelines[selectedTimeline];
  const lastSnapshot = timeline?.belief_state_snapshots.slice(-1)[0];

  if (isRunning) {
    return <ProgressOverlay progress={progress} onCancel={onCancel} />;
  }

  if (status === "failed") {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <p className="font-[family-name:var(--font-syne)] text-xl font-bold text-red-400">
            Simulation failed
          </p>
          <p className="mt-2 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/40">
            Something went wrong. Please try again.
          </p>
        </div>
      </div>
    );
  }

  if (!results || !timeline) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/30">
          Loading simulation data...
        </p>
      </div>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "thoughts_a", label: "Your Thoughts" },
    { key: "dialogue", label: "Dialogue" },
    { key: "risk", label: "Risk" },
  ];

  return (
    <div>
      {/* Timeline selector */}
      <div className="mb-4">
        <TimelineSelector
          timelines={results.timelines}
          selectedIndex={selectedTimeline}
          onSelect={setSelectedTimeline}
        />
      </div>

      {/* Mobile tabs */}
      <div className="mb-4 flex gap-1 rounded-lg bg-[#060d14] p-1 md:hidden">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setMobileTab(tab.key)}
            className={`flex-1 rounded-md py-2 font-[family-name:var(--font-space-mono)] text-xs transition-all ${
              mobileTab === tab.key
                ? "bg-[#00c8ff]/10 text-[#00c8ff]"
                : "text-[#e8f4ff]/40"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Desktop: Three-panel layout */}
      <div className="hidden md:grid md:grid-cols-[28%_44%_28%] md:gap-3">
        {/* Left: Agent A thoughts */}
        <div className="rounded-xl border border-[#162638] bg-[#060d14]/50 overflow-y-auto max-h-[calc(100vh-220px)]">
          <LiveThoughtStream
            snapshots={timeline.belief_state_snapshots}
            agentLabel="You"
          />
        </div>

        {/* Center: Dialogue */}
        <div className="flex flex-col rounded-xl border border-[#162638] bg-[#060d14]/50 max-h-[calc(100vh-220px)]">
          <div className="border-b border-[#162638] px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
                Turn {timeline.turns_total} ·{" "}
                {timeline.reached_homeostasis ? (
                  <span className="text-[#00ff9d]">Homeostasis</span>
                ) : (
                  <span className="text-[#ef4444]">Collapsed</span>
                )}
              </span>
            </div>
          </div>
          <DialogueTranscript transcript={timeline.full_transcript} />
        </div>

        {/* Right: Collapse risk + Agent B */}
        <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-220px)]">
          <div className="rounded-xl border border-[#162638] bg-[#060d14]/50">
            <CollapseRiskMeter
              risk={lastSnapshot?.risk ?? 0}
              riskLevel={lastSnapshot?.risk_level ?? "LOW"}
              signalBreakdown={lastSnapshot?.signal_breakdown}
            />
          </div>
          <div className="rounded-xl border border-[#162638] bg-[#060d14]/50 overflow-y-auto">
            <LiveThoughtStream
              snapshots={timeline.belief_state_snapshots}
              agentLabel="Partner"
            />
          </div>
        </div>
      </div>

      {/* Mobile: Single panel */}
      <div className="md:hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={mobileTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="rounded-xl border border-[#162638] bg-[#060d14]/50 min-h-[400px]"
          >
            {mobileTab === "thoughts_a" && (
              <LiveThoughtStream
                snapshots={timeline.belief_state_snapshots}
                agentLabel="You"
              />
            )}
            {mobileTab === "dialogue" && (
              <DialogueTranscript transcript={timeline.full_transcript} />
            )}
            {mobileTab === "risk" && (
              <CollapseRiskMeter
                risk={lastSnapshot?.risk ?? 0}
                riskLevel={lastSnapshot?.risk_level ?? "LOW"}
                signalBreakdown={lastSnapshot?.signal_breakdown}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
