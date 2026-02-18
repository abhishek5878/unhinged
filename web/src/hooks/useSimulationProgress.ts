"use client";

import { useEffect, useRef, useCallback } from "react";
import { useSimulationStore } from "@/lib/simulation-store";
import type { SimulationProgress } from "@/types/simulation";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000";
const MAX_RETRIES = 3;

export function useSimulationProgress(simulationId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const { updateProgress, setStatus, status, progress } =
    useSimulationStore();

  const connect = useCallback(() => {
    if (!simulationId) return;

    setStatus("connecting");
    const ws = new WebSocket(
      `${WS_BASE}/simulate/${simulationId}/progress`
    );
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
      setStatus("running");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.heartbeat) return;
        updateProgress(data as SimulationProgress);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (
        retriesRef.current < MAX_RETRIES &&
        status !== "completed" &&
        status !== "failed"
      ) {
        retriesRef.current += 1;
        const delay = Math.min(1000 * 2 ** retriesRef.current, 8000);
        setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [simulationId, updateProgress, setStatus, status]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  return { status, progress };
}
