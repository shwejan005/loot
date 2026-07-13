# Loot — Your Coding Memory. Powered by AI.

An AI-native learning platform that automatically transforms every accepted coding
solution into a personalized knowledge asset. Loot observes coding activity, analyzes
implementation choices, builds structured notes, identifies learning patterns, and
guides users toward long-term mastery.

> Most coding platforms answer *"How many problems have you solved?"*. Loot answers
> *"What have you actually learned?"*.

## Vision

Loot is the personal operating system for algorithmic learning. Every accepted submission
is automatically converted into structured documentation, AI-generated explanations,
revision material, analytics, and long-term learning history.

## Core Features

- Background synchronization of accepted submissions.
- AI-generated explanations based on the user's exact implementation.
- Automatic knowledge pages for every solved problem.
- Topic-wise organization (Arrays, Graphs, DP, Trees, etc.).
- Daily AI journals and structured dashboards.
- Learning analytics identifying strengths, weaknesses, and recurring mistakes.
- Intelligent revision scheduling using learning history.
- Interview readiness scoring based on coverage, consistency, and solution quality.

## Technology Stack

- **Frontend:** Next.js, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, PostgreSQL, Redis
- **AI:** Large Language Models, embeddings, retrieval-based personalization
- **Infrastructure:** Background workers, queues, event-driven synchronization

## Repository Layout

```
loot/
├── frontend/   # Next.js web app (dashboard, knowledge pages, analytics)
├── backend/    # FastAPI service, workers, AI analysis pipeline
├── shared/     # Shared contracts / types between frontend and backend
└── docs/       # Architecture, ADRs, and onboarding docs
```

## Getting Started

See `backend/README.md` and `frontend/README.md` for setup instructions.

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Roadmap

Multiple coding platforms, AI mock interviews, personalized roadmaps, mentor workspaces,
IDE integration, recruiter-ready technical portfolios, and mobile learning experiences.
