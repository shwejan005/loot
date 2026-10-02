"""Loot Wallet API entry point.

Smart card routing engine that maximises credit card rewards.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import engine, Base
from app.routers import auth, cards, catalog, transactions, routing, analytics

logger = logging.getLogger("loot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: auto-create tables. Disable in production.
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)

    # Seed on every startup; the seeder is idempotent and also runs when
    # deployment schema creation is handled separately by Alembic.
    try:
        from app.seed.load import seed_cards
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            seed_cards(db)
        finally:
            db.close()
        logger.info("Card catalog seed complete")
    except Exception as e:
        logger.warning("Card catalog seed skipped or failed: %s", e)

    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered smart wallet that maximises credit card rewards.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(catalog.router)
app.include_router(transactions.router)
app.include_router(routing.router)
app.include_router(analytics.router)


# ── Global exception handler ────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}
