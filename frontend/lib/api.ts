import * as React from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface User {
  id: number;
  username: string;
  email?: string | null;
  created_at: string;
}

export interface KnowledgePage {
  id: number;
  problem_id: number;
  explanation?: string | null;
  revision_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Readiness {
  user_id: number;
  solved_count: number;
  analyzed_count: number;
  topics_covered: number;
  readiness_score: number;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
