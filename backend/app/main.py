from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import engine, Base
from app.routers import users, submissions, knowledge, analytics, connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local-dev convenience: auto-create tables. For production, disable this
    # and manage schema with `alembic upgrade head`.
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.include_router(users.router)
app.include_router(submissions.router)
app.include_router(knowledge.router)
app.include_router(analytics.router)
app.include_router(connections.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.environment}
