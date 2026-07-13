"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchJson, type Readiness } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<Readiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState(1);

  useEffect(() => {
    fetchJson<Readiness>(`/analytics/users/${userId}/readiness`)
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [userId]);

  return (
    <main className="min-h-screen">
      <NavBar />
      <section className="container py-12">
        <h1 className="text-3xl font-bold tracking-tight">Interview Readiness</h1>
        <p className="mt-2 text-muted-foreground">
          Composite score from solution coverage, analysis depth, and topic breadth.
        </p>

        {error && (
          <p className="mt-8 rounded border border-destructive/40 bg-destructive/10 p-4 text-sm">
            Could not reach the API. Start the backend on port 8000. ({error})
          </p>
        )}

        {data && (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">Readiness</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-bold">{data.readiness_score}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">Solved</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-bold">{data.solved_count}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">Analyzed</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-bold">{data.analyzed_count}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-muted-foreground">Topics</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-bold">{data.topics_covered}</CardContent>
            </Card>
          </div>
        )}
      </section>
    </main>
  );
}
