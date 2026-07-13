# Loot Frontend

Next.js dashboard for the Loot coding-memory platform.

## Stack

- **Framework:** Next.js 14 (App Router) + TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui style primitives (`components/ui`)
- **Icons:** lucide-react

## Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE if needed
npm run dev
```

App runs at `http://localhost:3000`. Pages:

- `/` — landing + feature overview
- `/knowledge` — per-problem AI knowledge pages
- `/analytics` — interview readiness dashboard

## Environment

| Variable                | Default                  |
|-------------------------|--------------------------|
| `NEXT_PUBLIC_API_BASE`  | `http://localhost:8000`  |
