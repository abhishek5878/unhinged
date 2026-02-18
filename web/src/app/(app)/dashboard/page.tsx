"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { MatchCard } from "@/components/dashboard/MatchCard";
import { PastSimulationsTable } from "@/components/dashboard/PastSimulationsTable";
import { mockCandidates, mockPastSimulations } from "@/lib/mock-data";
import { createSimulation } from "@/lib/api";
import type { MatchCandidate } from "@/types/simulation";

export default function DashboardPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [candidates, setCandidates] = useState(mockCandidates);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function handleSimulate(candidate: MatchCandidate) {
    setLoadingId(candidate.user_id);
    try {
      const token = await getToken();
      if (!token) return;

      const result = await createSimulation(
        token,
        "current-user-id",
        candidate.user_id
      );
      router.push(`/dashboard/simulation/${result.simulation_id}`);
    } catch (error) {
      console.error("Failed to start simulation:", error);
      setLoadingId(null);
    }
  }

  function handleSkip(userId: string) {
    setCandidates((prev) => prev.filter((c) => c.user_id !== userId));
  }

  return (
    <div className="mx-auto max-w-5xl space-y-12">
      {/* Queue section */}
      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          Your Queue
        </p>
        <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          Simulation candidates
        </h1>
        <p className="mt-1 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/40">
          Curated for maximum simulation signal — not maximum similarity.
        </p>

        {candidates.length > 0 ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {candidates.map((candidate) => (
              <MatchCard
                key={candidate.user_id}
                candidate={candidate}
                onSimulate={() => handleSimulate(candidate)}
                onSkip={() => handleSkip(candidate.user_id)}
                loading={loadingId === candidate.user_id}
              />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-[#162638] bg-[#060d14]/30 p-12 text-center">
            <p className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/30">
              No more candidates in your queue. Check back soon.
            </p>
          </div>
        )}
      </section>

      {/* Past simulations */}
      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#e8f4ff]/30">
          History
        </p>
        <h2 className="mb-6 font-[family-name:var(--font-syne)] text-xl font-bold text-[#e8f4ff]">
          Past Simulations
        </h2>
        <PastSimulationsTable simulations={mockPastSimulations} />
      </section>
    </div>
  );
}
