"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { SimulationReport } from "@/components/report/SimulationReport";
import { getSimulation, getSimulationReport } from "@/lib/api";
import { generateMockResults } from "@/lib/mock-data";
import type { SimulationResults } from "@/types/simulation";

export default function ReportPage() {
  const params = useParams();
  const { getToken } = useAuth();
  const simulationId = params.id as string;

  const [results, setResults] = useState<SimulationResults | null>(null);
  const [reportText, setReportText] = useState("");
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const token = await getToken();
        if (!token) throw new Error("No token");

        const [simData, reportData] = await Promise.all([
          getSimulation(token, simulationId),
          getSimulationReport(token, simulationId).catch(() => ({
            simulation_id: simulationId,
            report: "",
          })),
        ]);

        if (simData.results) {
          setResults(simData.results);
        } else {
          setIsDemo(true);
          setResults(generateMockResults());
        }
        setReportText(reportData.report);
      } catch {
        // Fallback to mock data for demo
        setIsDemo(true);
        setResults(generateMockResults());
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [simulationId, getToken]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30">
            Loading report...
          </p>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/30">
          No simulation data available.
        </p>
      </div>
    );
  }

  return (
    <div>
      {isDemo && (
        <div className="mx-auto mb-6 max-w-[820px] rounded-lg border border-[#fbbf24]/30 bg-[#fbbf24]/5 px-4 py-3">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#fbbf24]">
            DEMO MODE — This report uses sample data. Run a real simulation to
            see your actual compatibility analysis.
          </p>
        </div>
      )}
      <SimulationReport
        simulationId={simulationId}
        results={results}
        reportText={reportText}
      />
    </div>
  );
}
