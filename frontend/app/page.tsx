import { NavBar } from "@/components/nav-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "AI Explanations",
    body: "Every accepted solution is explained based on your exact implementation.",
  },
  {
    title: "Knowledge Pages",
    body: "Automatic, searchable documentation for every problem you solve.",
  },
  {
    title: "Topic Organization",
    body: "Problems grouped into Arrays, Graphs, DP, Trees, and more.",
  },
  {
    title: "Learning Analytics",
    body: "Strengths, weaknesses, and recurring mistakes surfaced automatically.",
  },
  {
    title: "Revision Scheduling",
    body: "Spaced-repetition prompts built from your own learning history.",
  },
  {
    title: "Readiness Score",
    body: "Interview readiness from coverage, consistency, and solution quality.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <NavBar />
      <section className="container py-16">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight">
          What have you actually learned?
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
          Loot is an autonomous AI learning companion that captures, organizes, and explains
          every accepted solution — so each solved problem becomes a permanent step toward
          technical mastery.
        </p>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title}>
              <CardHeader>
                <CardTitle>{f.title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{f.body}</CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
