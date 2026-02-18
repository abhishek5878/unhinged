const steps = [
  {
    number: "01",
    title: "Create Your Profile",
    description:
      "Answer questions about your values, attachment style, communication patterns, and what you fear most in relationships. We build your Shadow Vector.",
  },
  {
    number: "02",
    title: "We Simulate 100+ Futures",
    description:
      "Our Monte Carlo engine runs parallel relationship timelines, injecting Black Swan crises (job loss, family emergencies, trust ruptures) to stress-test your compatibility.",
  },
  {
    number: "03",
    title: "Get Your Compatibility Report",
    description:
      "Receive a detailed analysis: homeostasis rate, antifragility score, collapse risk factors, and specific crisis axes where your relationship is most vulnerable.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-muted/50 py-24 sm:py-32">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Three steps to understanding your relational future.
          </p>
        </div>
        <div className="mx-auto mt-16 grid max-w-4xl gap-12 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.number} className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
                {step.number}
              </div>
              <h3 className="mt-6 text-xl font-semibold">{step.title}</h3>
              <p className="mt-3 text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
