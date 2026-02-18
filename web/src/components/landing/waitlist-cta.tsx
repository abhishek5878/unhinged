import Link from "next/link";
import { Button } from "@/components/ui/button";

export function WaitlistCTA() {
  return (
    <section className="py-24 sm:py-32">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-2xl rounded-2xl bg-primary p-12 text-center text-primary-foreground">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Ready to Know Your Future?
          </h2>
          <p className="mt-4 text-lg text-primary-foreground/80">
            Join the waitlist for early access. Be among the first to experience
            AI-powered relationship prediction.
          </p>
          <div className="mt-8">
            <Link href="/waitlist">
              <Button
                size="lg"
                variant="secondary"
                className="text-base px-8"
              >
                Join the Waitlist
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
