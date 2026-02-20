"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { SimulationViewer } from "@/components/simulation/SimulationViewer";
import { useSimulationProgress } from "@/hooks/useSimulationProgress";
import { getSimulation, cancelSimulation } from "@/lib/api";
import { generateMockResults } from "@/lib/mock-data";
import type { SimulationResults } from "@/types/simulation";

export default function SimulationPage() {
  const params = useParams();
  const { getToken } = useAuth();
  const simulationId = params.id as string;

  const { status: wsStatus, progress } = useSimulationProgress(simulationId);
  const [results, setResults] = useState<SimulationResults | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [status, setStatus] = useState<
    "connecting" | "running" | "completed" | "failed" | "idle"
  >("connecting");

  // Sync WS status
  useEffect(() => {
    if (wsStatus === "completed" || wsStatus === "failed") {
      setStatus(wsStatus);
    } else if (wsStatus === "running") {
      setStatus("running");
    }
  }, [wsStatus]);

  // Fetch results when completed
  useEffect(() => {
    if (status !== "completed" || results) return;

    async function fetchResults() {
      try {
        const token = await getToken();
        if (!token) return;
        const sim = await getSimulation(token, simulationId);
        if (sim.results) {
          setResults(sim.results);
          return;
        }
      } catch {
        // Backend unavailable
      }
      // Fallback to mock data
      setIsDemo(true);
      setResults(generateMockResults());
    }

    fetchResults();
  }, [status, results, simulationId, getToken]);

  // If WS never connects after 10s, show demo data with banner
  useEffect(() => {
    const timer = setTimeout(() => {
      if (status === "connecting") {
        setStatus("completed");
        setIsDemo(true);
        setResults(generateMockResults());
      }
    }, 10000);
    return () => clearTimeout(timer);
  }, [status]);

  async function handleCancel() {
    try {
      const token = await getToken();
      if (token) {
        await cancelSimulation(token, simulationId);
      }
    } catch {
      // ignore
    }
    setStatus("failed");
  }

  return (
    <div className="mx-auto max-w-6xl">
      {/* Demo mode banner */}
      {isDemo && (
        <div className="mb-4 rounded-lg border border-[#fbbf24]/30 bg-[#fbbf24]/5 px-4 py-3">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#fbbf24]">
            DEMO MODE — Showing sample simulation data. Connect your backend for
            real results.
          </p>
        </div>
      )}

      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
            Simulation
          </p>
          <h1 className="font-[family-name:var(--font-syne)] text-xl font-bold text-[#e8f4ff]">
            Live Viewer
          </h1>
        </div>
        {status === "completed" && (
          <Link
            href={`/dashboard/simulation/${simulationId}/report`}
            className="rounded-lg bg-[#00c8ff] px-5 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90"
          >
            View Full Report →
          </Link>
        )}
      </div>

      <SimulationViewer
        status={status}
        progress={progress}
        results={results}
        onCancel={handleCancel}
      />
    </div>
  );
}
