import { Brain, GitBranch, BarChart3, MessageSquare } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const features = [
  {
    icon: Brain,
    title: "Theory of Mind Engine",
    description:
      "Recursive L0-L3 epistemic tracking models what each partner truly believes, what they think the other believes, and the meta-beliefs beyond.",
  },
  {
    icon: GitBranch,
    title: "Monte Carlo Simulation",
    description:
      "100+ parallel relationship timelines are simulated with targeted crisis injection to stress-test compatibility under real-world pressure.",
  },
  {
    icon: BarChart3,
    title: "Collapse Early Warning",
    description:
      "Real-time detection of belief divergence, linguistic withdrawal, and defensive attribution patterns before relationships reach the point of no return.",
  },
  {
    icon: MessageSquare,
    title: "Linguistic Pattern Analysis",
    description:
      "Tracks convergence of communication signatures, Hinglish takiya-kalaam adoption, and narrative coherence as markers of relational alignment.",
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 sm:py-32">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Built on Science, Not Vibes
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Our Relational Foundation Model combines computational
            psychometrics with multi-agent simulation.
          </p>
        </div>
        <div className="mx-auto mt-16 grid max-w-5xl gap-6 sm:grid-cols-2">
          {features.map((feature) => (
            <Card key={feature.title} className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <feature.icon className="h-10 w-10 text-primary mb-2" />
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
