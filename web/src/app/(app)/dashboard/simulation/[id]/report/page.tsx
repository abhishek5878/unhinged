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
          // Fallback to mock data
          setResults(generateMockResults());
        }
        setReportText(reportData.report);
      } catch {
        // Fallback to mock data for demo
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
    <SimulationReport
      simulationId={simulationId}
      results={results}
      reportText={reportText}
    />
  );
}
