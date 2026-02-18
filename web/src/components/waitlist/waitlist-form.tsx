"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { joinWaitlist } from "@/lib/api";

export function WaitlistForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const refCode = searchParams.get("ref");

  const [email, setEmail] = useState("");
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await joinWaitlist({
        email,
        city: city || "Other",
        ref: refCode || undefined,
        source: "waitlist_page",
      });

      router.push(
        `/match/waitlist?code=${result.referral_code}&email=${encodeURIComponent(email)}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="arjun@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="city">City</Label>
        <Input
          id="city"
          type="text"
          placeholder="Mumbai"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          required
        />
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      <Button type="submit" className="w-full" size="lg" disabled={loading}>
        {loading ? "Joining..." : "Join the Waitlist"}
      </Button>
    </form>
  );
}
