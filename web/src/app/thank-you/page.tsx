"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function ThankYouContent() {
  const searchParams = useSearchParams();
  const position = searchParams.get("position") || "?";
  const referral = searchParams.get("referral") || "";

  const referralLink =
    typeof window !== "undefined"
      ? `${window.location.origin}/waitlist?ref=${referral}`
      : "";

  function copyReferral() {
    navigator.clipboard.writeText(referralLink);
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">You&apos;re In!</CardTitle>
        <CardDescription>
          You&apos;ve been added to the PRELUDE waitlist.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Your position</p>
          <p className="text-6xl font-bold text-primary">#{position}</p>
        </div>

        {referral && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Share your referral link</p>
            <div className="flex gap-2">
              <code className="flex-1 truncate rounded-md border bg-muted px-3 py-2 text-sm">
                {referralLink}
              </code>
              <Button variant="outline" size="sm" onClick={copyReferral}>
                Copy
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Share with friends to move up the waitlist.
            </p>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <Link href="/sign-up">
            <Button className="w-full" variant="outline">
              Create Account to Track Your Position
            </Button>
          </Link>
          <Link href="/">
            <Button className="w-full" variant="ghost">
              Back to Home
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ThankYouPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <Suspense
        fallback={<div className="h-96 w-full max-w-md animate-pulse bg-muted rounded-lg" />}
      >
        <ThankYouContent />
      </Suspense>
    </div>
  );
}
