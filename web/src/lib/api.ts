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
