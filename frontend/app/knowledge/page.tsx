"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchJson, type KnowledgePage } from "@/lib/api";

export default function KnowledgePage() {
  const [page, setPage] = useState<KnowledgePage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problemId, setProblemId] = useState(1);

  useEffect(() => {
    fetchJson<KnowledgePage>(`/knowledge/pages/${problemId}`)
      .then(setPage)
      .catch((e) => setError(String(e)));
  }, [problemId]);

  return (
    <main className="min-h-screen">
      <NavBar />
      <section className="container py-12">
        <h1 className="text-3xl font-bold tracking-tight">Knowledge Pages</h1>
        <p className="mt-2 text-muted-foreground">
          AI-generated documentation for every solved problem.
        </p>

        <div className="mt-6 flex items-center gap-2">
          <label className="text-sm text-muted-foreground" htmlFor="pid">
            Problem ID
          </label>
          <input
            id="pid"
            type="number"
            value={problemId}
            onChange={(e) => setProblemId(Number(e.target.value))}
            className="h-9 w-24 rounded-md border border-input bg-background px-3 text-sm"
          />
        </div>

        {error && (
          <p className="mt-8 rounded border border-destructive/40 bg-destructive/10 p-4 text-sm">
            No knowledge page yet for problem {problemId}. ({error})
          </p>
        )}

        {page && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Problem #{page.problem_id}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <div className="font-medium">Explanation</div>
                <p className="mt-1 text-muted-foreground">{page.explanation}</p>
              </div>
              <div>
                <div className="font-medium">Revision notes</div>
                <p className="mt-1 text-muted-foreground">{page.revision_notes}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </section>
    </main>
  );
}
