# Shared

Contracts and types shared between the Loot frontend and backend.

This directory is the single source of truth for API shapes, event schemas, and
domain vocabulary (topics, readiness scoring inputs, sync payloads). As the project
matures, prefer generating client/server bindings from a shared OpenAPI spec here
rather than duplicating models in `frontend/` and `backend/`.
