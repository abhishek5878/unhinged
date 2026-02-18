import { Suspense } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WaitlistForm } from "@/components/waitlist/waitlist-form";

export default function WaitlistPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <Link href="/" className="mb-4 text-xl font-bold tracking-tight">
            <span className="text-primary">APRIORI</span>{" "}
            <span className="text-muted-foreground">MATCH</span>
          </Link>
          <CardTitle className="text-2xl">Join the Waitlist</CardTitle>
          <CardDescription>
            Be among the first to experience AI-powered relationship prediction.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<div className="h-64 animate-pulse bg-muted rounded" />}>
            <WaitlistForm />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
