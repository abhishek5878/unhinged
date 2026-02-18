import { Navbar } from "@/components/landing/navbar";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { HowItWorks } from "@/components/landing/how-it-works";
import { WaitlistCTA } from "@/components/landing/waitlist-cta";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <WaitlistCTA />
      <Footer />
    </div>
  );
}
