"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
import { MatchCard } from "@/components/dashboard/MatchCard";
import { PastSimulationsTable } from "@/components/dashboard/PastSimulationsTable";
import {
  mockCandidates,
  mockPastSimulations,
} from "@/lib/mock-data";
import {
  createSimulation,
  getCompatibilityCandidates,
  getMySimulations,
} from "@/lib/api";
import type { MatchCandidate, PastSimulation } from "@/types/simulation";

// Map API candidate to MatchCandidate shape (supplement missing display fields with defaults)
function mapApiCandidate(c: {
  user_id: string;
  attachment_style: string;
  communication_style: string;
  similarity_score: number;
}, idx: number): MatchCandidate {
  const mock = mockCandidates[idx % mockCandidates.length];
  return {
    user_id: c.user_id,
    first_name: mock.first_name,
    city: mock.city,
    attachment_style: (c.attachment_style as MatchCandidate["attachment_style"]) || mock.attachment_style,
    shared_vulnerability_hint: mock.shared_vulnerability_hint,
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { user } = useUser();

  const [candidates, setCandidates] = useState<MatchCandidate[]>([]);
  const [pastSims, setPastSims] = useState<PastSimulation[]>(mockPastSimulations);
  const [loadingCandidates, setLoadingCandidates] = useState(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  const userId = (user?.publicMetadata as { user_id?: string })?.user_id;

  useEffect(() => {
    if (!userId) return;

    async function loadData() {
      setLoadingCandidates(true);
      try {
        const token = await getToken();
        if (!token) throw new Error("No token");

        // Check onboarding status
        const meRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend"}/auth/me`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (meRes.ok) {
          const me = await meRes.json();
          if (!me.has_shadow_vector) {
            router.push("/onboarding");
            return;
          }
        }

        // Fetch real candidates
        const [candidatesData, simsData] = await Promise.allSettled([
          getCompatibilityCandidates(token, userId!),
          getMySimulations(token, userId!),
        ]);

        if (
          candidatesData.status === "fulfilled" &&
          candidatesData.value.candidates.length > 0
        ) {
          setCandidates(
            candidatesData.value.candidates.map((c, i) => mapApiCandidate(c, i))
          );
          setIsDemo(false);
        } else {
          // No real candidates yet — show mock queue in demo mode
          setCandidates(mockCandidates);
          setIsDemo(true);
        }

        if (simsData.status === "fulfilled") {
          // Map API simulations to PastSimulation shape
          const mapped = simsData.value.map((s) => ({
            simulation_id: s.simulation_id,
            partner_name: "—",
            date: s.created_at,
            homeostasis_rate: s.homeostasis_rate ?? 0,
            primary_risk: s.primary_collapse_vector ?? "—",
            status: s.status as PastSimulation["status"],
          }));
          if (mapped.length > 0) setPastSims(mapped);
        }
      } catch {
        setCandidates(mockCandidates);
        setIsDemo(true);
      } finally {
        setLoadingCandidates(false);
      }
    }

    loadData();
  }, [userId, getToken, router]);

  async function handleSimulate(candidate: MatchCandidate) {
    if (!userId) {
      setError("Your profile isn't set up yet. Please complete onboarding first.");
      return;
    }

    setLoadingId(candidate.user_id);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("Session expired. Please sign in again.");
        setLoadingId(null);
        return;
      }

      const result = await createSimulation(token, userId, candidate.user_id);
      router.push(`/dashboard/simulation/${result.simulation_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start simulation");
      setLoadingId(null);
    }
  }

  function handleSkip(candidateUserId: string) {
    setCandidates((prev) => prev.filter((c) => c.user_id !== candidateUserId));
  }

  return (
    <div className="mx-auto max-w-5xl space-y-12">
      {/* Demo mode banner */}
      {isDemo && !loadingCandidates && (
        <div className="rounded-lg border border-[#fbbf24]/30 bg-[#fbbf24]/5 px-4 py-3">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#fbbf24]">
            DEMO MODE — Showing sample candidates. Real matches appear once more
            users complete onboarding.
          </p>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="rounded-lg border border-[#ef4444]/30 bg-[#ef4444]/5 px-4 py-3 flex items-center justify-between">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#ef4444]">
            {error}
          </p>
          <button
            onClick={() => setError(null)}
            className="ml-4 text-[#ef4444]/60 hover:text-[#ef4444] text-xs"
          >
            ✕
          </button>
        </div>
      )}

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

        {loadingCandidates ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-52 animate-pulse rounded-xl border border-[#162638] bg-[#060d14]/30"
              />
            ))}
          </div>
        ) : candidates.length > 0 ? (
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
        <PastSimulationsTable simulations={pastSims} />
      </section>
    </div>
  );
}
