# AIC API Completion Implementation Plan

**Goal:** Expose the persisted AIC conversation and request data through documented FastAPI endpoints.

**Architecture:** Keep the existing ChatService write path unchanged. Add read-only SQLAlchemy queries in the FastAPI route layer and typed Pydantic response models; return structured 404 errors for unknown identifiers.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, Docker Compose.

**Scope:** `GET /health`, `POST /api/chat`, `GET /api/conversations/{conversation_id}`, `GET /api/conversations/{conversation_id}/messages`, and `GET /api/requests/{request_id}`. No authentication, deletion, streaming, or model-selection changes.

- [ ] Add response schemas and failing route contract checks.
- [ ] Implement read-only routes and structured not-found handling.
- [ ] Build the AIC image and verify OpenAPI contains all routes.
- [ ] Live-check conversation and request lookups against the running Compose PostgreSQL.
- [ ] Update the demo runbook with curl examples.
