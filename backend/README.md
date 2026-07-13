# Loot Backend

FastAPI service powering the AI-native coding memory platform.

## Stack

- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL (SQLAlchemy 2.0, Alembic migrations)
- **Cache / Queue:** Redis
- **AI:** OpenAI-compatible LLM + embeddings (configurable)

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in DATABASE_URL, REDIS_URL, OPENAI_API_KEY
uvicorn app.main:app --reload
```

The API docs are available at `http://localhost:8000/docs`.

## Layout

```
app/
├── main.py              # FastAPI app + router wiring
├── config.py            # Pydantic settings (env-driven)
├── db.py                # Engine, session, declarative base
├── models.py            # ORM models (User, Problem, Submission, ...)
├── schemas.py           # Pydantic request/response models
├── routers/             # users, submissions, knowledge, analytics, connections
├── ai/analyzer.py       # LLM explanation + embedding pipeline
├── platforms/           # platform clients (codeforces, leetcode) + registry
└── services/sync.py     # background submission sync worker
```


## How analysis works

When an accepted submission is created:

1. `routers/submissions.py` triggers `ai.analyzer.analyze_submission`.
2. The user's exact code + problem context is sent to the LLM.
3. A structured `SubmissionAnalysis` (approach, complexity, insight, mistakes)
   and an embedding vector are persisted.
4. A `KnowledgePage` is created/updated for revision and retrieval.

## Database migrations (Alembic)

For local dev, tables are auto-created on startup (`CREATE_TABLES_ON_STARTUP=true`).
For team/production, disable auto-create and manage schema with Alembic:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The initial migration (`alembic/versions/0001_initial.py`) creates every table in
`app/models.py`.

## Connecting a platform

1. Create a user: `POST /users`.
2. Register a connection: `POST /connections`
   (`{ "user_id": 1, "platform": "codeforces", "external_username": "tourist" }`).
3. Trigger sync: `POST /connections/sync` (or run the worker below).

Supported platforms: `codeforces` (public API, no auth) and `leetcode`
(requires `LEETCODE_SESSION` cookie for private history). Each platform normalizes
its submissions into `NormalizedSubmission`, which the worker upserts into
`Problem`/`Submission`, links `Topic`s, and analyzes accepted solutions.

## Running the sync worker

```bash
python -m app.services.sync
```

## Environment variables

| Variable                      | Default                                  |
|-------------------------------|------------------------------------------|
| `DATABASE_URL`                | `postgresql+psycopg2://.../loot`         |
| `REDIS_URL`                   | `redis://localhost:6379/0`               |
| `OPENAI_API_KEY`              | `""` (heuristic fallback if empty)       |
| `OPENAI_MODEL`                | `gpt-4o-mini`                            |
| `EMBEDDING_MODEL`             | `text-embedding-3-small`                 |
| `SYNC_POLL_INTERVAL_SECONDS`  | `30`                                     |
| `SYNC_BATCH_SIZE`             | `50`                                     |
| `LEETCODE_SESSION`            | `""`                                     |
| `CREATE_TABLES_ON_STARTUP`    | `true`                                   |
