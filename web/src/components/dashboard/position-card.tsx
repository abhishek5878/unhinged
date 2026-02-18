"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { WaitlistPositionResponse } from "@/lib/api";

interface PositionCardProps {
  data: WaitlistPositionResponse;
}

export function PositionCard({ data }: PositionCardProps) {
  const [copied, setCopied] = useState(false);

  const referralLink =
    typeof window !== "undefined"
      ? `${window.location.origin}/waitlist?ref=${data.referral_code}`
      : "";

  function copyReferral() {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Your Waitlist Position</CardTitle>
        <CardDescription>{data.email}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="text-center">
          <p className="text-7xl font-bold text-primary">#{data.position}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            of {data.total_signups} total signups
          </p>
        </div>

        <div className="flex justify-center">
          <Badge
            variant={data.status === "invited" ? "default" : "secondary"}
          >
            {data.status}
          </Badge>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">Your referral code</p>
          <div className="flex gap-2">
            <code className="flex-1 truncate rounded-md border bg-muted px-3 py-2 text-sm font-mono">
              {data.referral_code}
            </code>
            <Button variant="outline" size="sm" onClick={copyReferral}>
              {copied ? "Copied!" : "Copy Link"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
