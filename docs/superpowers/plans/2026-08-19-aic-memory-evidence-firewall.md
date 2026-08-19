# AIC Memory Evidence Firewall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent historical incident memory from being presented as current evidence while retaining it as investigation guidance after live evidence exists.

**Architecture:** Add a deterministic memory policy in front of Mem0: iteration one never recalls memory, later iterations derive an incident signature from current command outputs, filter candidates by failure reason and score, and inject accepted memories in an explicitly historical prompt section. Engineer-approved resolutions are indexed as diagnostic guidance with structured metadata.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL 18, Mem0 OSS, Qdrant, HolmesGPT, Docker Compose.

**Spec:** Conversation-approved design from 2026-08-19: AIC API remains the sole user flow; memory is an internal, evidence-gated implementation detail.

## Global Constraints

- The public `POST /api/chat` request contract remains compatible.
- Iteration one must return no memory references.
- Historical memory must never be labeled current evidence.
- Only engineer-approved memories are eligible.
- Existing PostgreSQL and Qdrant data must be preserved.

### Task 1: Deterministic memory policy

**Files:**
- Create: `deploy/demo/aic-api/src/aic/memory_policy.py`
- Create: `deploy/demo/aic-api/tests/test_memory_policy.py`

- [x] Write RED tests for iteration-one suppression, failure-reason extraction, score filtering, and mismatch rejection.
- [x] Run tests and observe missing-module/function failures.
- [x] Implement minimal pure policy helpers.
- [x] Run tests until GREEN and refactor names.

### Task 2: Evidence-gated retrieval and prompt

**Files:**
- Modify: `deploy/demo/aic-api/src/aic/config.py`
- Modify: `deploy/demo/aic-api/src/aic/memory.py`
- Modify: `deploy/demo/aic-api/src/aic/service.py`

- [x] Apply policy before Mem0 search and candidate injection.
- [x] Label memory as historical guidance and prohibit it from proving claims.
- [x] Preserve current-evidence provenance in the Holmes prompt.
- [x] Run focused policy tests and compile checks.

### Task 3: Guidance-oriented approved resolutions

**Files:**
- Modify: `deploy/demo/aic-api/src/aic/main.py`
- Modify: `deploy/demo/aic-api/src/aic/schemas.py`
- Modify: `deploy/demo/aic-api/src/aic/models.py`
- Create: `deploy/demo/aic-api/migrations/versions/0003_resolution_signature.py`

- [x] Add optional incident signature fields to approval requests and persistence.
- [x] Index approved memory as checks, anti-patterns, and historical outcome with metadata.
- [x] Re-index the CKAD-LIFE-002 resolution without deleting PostgreSQL conversation history.

### Task 4: Live verification

**Files:**
- Modify: `deploy/demo/README.md`
- Create: `docs/testing/holmesgpt/CKAD-LIFE-002-AIC/memory-policy-rerun.md`

- [x] Build and restart only the AIC Compose services required by the change.
- [x] Reset the disposable CKAD-LIFE-002 namespace fixture.
- [x] Create a fresh conversation through AIC API.
- [x] Verify iteration one has zero memory references.
- [x] Submit live command outputs and verify only matching approved guidance is recalled.
- [x] Record each AIC answer, scores, unsupported claims, and remaining limitations.
- [x] Run compile, focused tests, OpenAPI, health, migration, and diff checks.
