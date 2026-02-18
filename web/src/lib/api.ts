const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

// ---------------------------------------------------------------------------
// WaitlistEntry (revamped)
// ---------------------------------------------------------------------------

export interface WaitlistEntryRequest {
  email: string;
  city: string;
  ref?: string;
  source?: string;
}

export interface WaitlistEntryResponse {
  email: string;
  city: string;
  position: number;
  referral_code: string;
  referral_count: number;
  total_signups: number;
}

export interface WaitlistCheckResponse {
  on_waitlist: boolean;
  position: number | null;
  referral_code: string | null;
  referral_count: number;
}

export async function joinWaitlist(
  data: WaitlistEntryRequest
): Promise<WaitlistEntryResponse> {
  const res = await fetch(`${BASE}/waitlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Signup failed" }));
    throw new Error(err.detail || "Signup failed");
  }
  return res.json();
}

export async function checkWaitlist(
  email: string
): Promise<WaitlistCheckResponse> {
  const res = await fetch(
    `${BASE}/waitlist/check?email=${encodeURIComponent(email)}`
  );
  if (!res.ok) {
    throw new Error("Failed to check waitlist");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Legacy waitlist (old WaitlistSignup model)
// ---------------------------------------------------------------------------

export interface WaitlistSignupRequest {
  email: string;
  name: string;
  partner_email?: string;
  referral_code_used?: string;
}

export interface WaitlistSignupResponse {
  id: string;
  email: string;
  name: string;
  partner_email: string | null;
  position: number;
  referral_code: string;
  status: string;
  created_at: string;
}

export interface WaitlistPositionResponse {
  email: string;
  position: number;
  referral_code: string;
  status: string;
  total_signups: number;
}

export async function getMyWaitlistPosition(
  token: string
): Promise<WaitlistPositionResponse> {
  const res = await fetch(`${BASE}/waitlist/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch position");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Simulation API
// ---------------------------------------------------------------------------

import type { SimulationStatus } from "@/types/simulation";

export async function createSimulation(
  token: string,
  userAId: string,
  userBId: string,
  nTimelines: number = 100
): Promise<{ simulation_id: string; status: string; eta_seconds: number }> {
  const res = await fetch(`${BASE}/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      user_a_id: userAId,
      user_b_id: userBId,
      n_timelines: nTimelines,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create simulation" }));
    throw new Error(err.detail || "Failed to create simulation");
  }
  return res.json();
}

export async function getSimulation(
  token: string,
  simulationId: string
): Promise<SimulationStatus> {
  const res = await fetch(`${BASE}/simulate/${simulationId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch simulation");
  }
  return res.json();
}

export async function getSimulationReport(
  token: string,
  simulationId: string
): Promise<{ simulation_id: string; report: string }> {
  const res = await fetch(`${BASE}/simulate/${simulationId}/report`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch report");
  }
  return res.json();
}

export async function cancelSimulation(
  token: string,
  simulationId: string
): Promise<void> {
  const res = await fetch(`${BASE}/simulate/${simulationId}/cancel`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to cancel simulation");
  }
}
