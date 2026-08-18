# POM-DESIGN-001 Human-Centric Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revise the PostOps Memory proposal so it describes a human-led DevOps copilot using PostgreSQL as the business source of truth and Mem0 OSS only as an optional extraction and retrieval engine.

**Architecture:** PostOps Memory orchestrates ticket context, HolmesGPT investigation, conversation history, engineer feedback, and resolution approval. The engineer's confirmed resolution is authoritative; PostgreSQL stores business records and approval state, while Mem0/Qdrant indexes only approved resolution documents for semantic candidate recall.

**Tech Stack:** Markdown, PostgreSQL, pgvector, Mem0 OSS, Qdrant embedded, HolmesGPT, LiteLLM, Kubernetes, Prometheus, Loki, Redmine (future integration).

**Spec:** `outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md`

## Global Constraints

- Story/task ID: `POM-DESIGN-001`.
- The engineer remains the final authority; POM is not required to diagnose correctly on the first response.
- PostgreSQL is the business system of record for tickets, conversations, feedback, resolutions, approvals, and Skill versions.
- Mem0 OSS is optional and limited to extraction, semantic candidate recall, and conversational assistance; it is not the approval or Skill-governance system.
- Only engineer-confirmed resolutions may be indexed as reusable operational memory.
- Similar wording is not proof of the same root cause; live evidence and an incident fingerprint must distinguish same-symptom/different-cause cases.
- HolmesGPT remains read-only in the PoC.
- Redmine implementation, autonomous remediation, production HA, and UI implementation are out of scope.
- No credentials, raw Secret values, authorization headers, or private telemetry are added to the repository.

---

### Task 1: Capture the documentation contract and observe RED

**Files:**
- Create: `docs/superpowers/plans/2026-08-18-pom-design-001-human-centric-memory.md`
- Test: `README.md`
- Test: `outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md`
- Test: `docs/testing/holmesgpt-memory-evaluation.md`
- Test: `docs/superpowers/plans/2026-08-18-holmesgpt-memory-evaluation.md`
- Test: `docs/testing/holmesgpt/README.md`
- Test: `docs/testing/holmesgpt/CKAD-LIFE-001/run-b-holmesgpt-memory.md`

**Interfaces:**
- Consumes: the current proposal and evaluation documents.
- Produces: an exact list of stale TencentDB-specific and AI-authoritative claims to remove or qualify.

- [ ] **Step 1: Run the RED terminology check**

  Run:

  ```bash
  rtk rg -n "TencentDB|triển khai nội bộ|quản lý Skill|HolmesGPT \+ TencentDB" README.md outputs docs/testing docs/superpowers/plans/2026-08-18-holmesgpt-memory-evaluation.md
  ```

  Expected: matches show that the proposal still treats TencentDB as an on-premise open-source memory and assigns approval/Skill governance to the memory backend.

- [ ] **Step 2: Record the expected GREEN contract**

  The final documents must explicitly state: POM assists rather than decides; engineers may provide the final correct resolution; raw conversations are retained for traceability; approved resolutions are separate from untrusted assistant output; PostgreSQL is authoritative; Mem0 is an optional derived index.

### Task 2: Revise the core innovation proposal

**Files:**
- Modify: `README.md`
- Modify: `outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md`

**Interfaces:**
- Consumes: the GREEN contract from Task 1.
- Produces: the canonical product positioning and end-to-end human-in-the-loop workflow used by all evaluation documents.

- [ ] **Step 1: Update the overview and technology roles**

  Replace TencentDB-specific positioning with an on-premise Agent Memory layer whose PoC candidate is Mem0 OSS. State that PostgreSQL owns the business records and that LiteLLM continues to serve HolmesGPT and memory extraction without requiring an embeddings route.

- [ ] **Step 2: Update objectives and design principles**

  Add that the AI may be incomplete or wrong during investigation, the engineer's confirmed resolution is authoritative, and POM's value includes evidence collection, conversation continuity, summarization, and organizational learning.

- [ ] **Step 3: Update the component and logical architecture sections**

  Define PostgreSQL, Mem0 OSS/Qdrant, an incident similarity pipeline, and the separation between raw conversation history and approved incident memory.

- [ ] **Step 4: Update the end-to-end workflow and minimal data model**

  Include iterative chat, scattered command/action extraction, engineer-authored corrections, draft resolution, approval, normalized incident fingerprint, and approved-memory publication.

- [ ] **Step 5: Update roadmap, metrics, risks, novelty, and conclusion**

  Measure assistance and human editing effort in addition to first-answer accuracy. Add hard-negative retrieval tests and prevent same-text/different-cause matches from being treated as confirmed equivalence.

### Task 3: Align the evaluation design and result templates

**Files:**
- Modify: `docs/testing/holmesgpt-memory-evaluation.md`
- Modify: `docs/superpowers/plans/2026-08-18-holmesgpt-memory-evaluation.md`
- Modify: `docs/testing/holmesgpt/README.md`
- Modify: `docs/testing/holmesgpt/CKAD-LIFE-001/README.md`
- Modify: `docs/testing/holmesgpt/CKAD-LIFE-001/run-b-holmesgpt-memory.md`
- Modify: `docs/infra/codex-handoff.md`

**Interfaces:**
- Consumes: the canonical product roles from Task 2.
- Produces: a provider-neutral `HolmesGPT + POM Memory` Run B contract implemented initially with Mem0 OSS.

- [ ] **Step 1: Rename Run B without falsifying historical results**

  Use `HolmesGPT + POM Memory (Mem0 OSS)` for the pending run. Keep Run A unchanged and do not invent Run B scores.

- [ ] **Step 2: Replace the TencentDB V3-specific contract**

  Define approved-resolution ingestion, PostgreSQL identifiers, Mem0 metadata, local FastEmbed embeddings, Qdrant storage, recall provenance, and fallback to HolmesGPT without memory.

- [ ] **Step 3: Add human-assistance evaluation dimensions**

  Record engineer corrections, number of useful investigation steps, time to confirmed resolution, summarization effort, retrieval relevance, anchoring, and hard-negative false positives.

- [ ] **Step 4: Update handoff state**

  Record that TencentDB is no longer the local PoC backend and that Mem0 remains a candidate whose value must be measured against direct PostgreSQL/pgvector retrieval.

### Task 4: Verify documentation integrity and prepare handoff

**Files:**
- Test: all files modified by Tasks 1–3.
- Runbook: `docs/runbooks/holmesgpt-evaluation-run-a.md` remains historical and must not be rewritten as a Mem0 run.

**Interfaces:**
- Consumes: revised Markdown documents.
- Produces: fresh verification evidence and a task-scoped commit proposal; no Git mutation without a separate explicit request.

- [ ] **Step 1: Run the GREEN terminology check**

  Run:

  ```bash
  rtk rg -n "TencentDB Agent Memory|HolmesGPT \+ TencentDB" README.md outputs docs/testing docs/infra/codex-handoff.md
  ```

  Expected: no active architecture or pending-run claim uses TencentDB; historical comparison text, if retained, is explicitly labelled historical.

- [ ] **Step 2: Verify required human-centric terms**

  Run:

  ```bash
  rtk rg -n "kỹ sư|PostgreSQL|Mem0|phê duyệt|resolution|fingerprint|same symptom|khác nguyên nhân" README.md outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md docs/testing/holmesgpt-memory-evaluation.md
  ```

  Expected: each major contract appears in the canonical proposal and evaluation design.

- [ ] **Step 3: Run formatting and secret checks**

  Run:

  ```bash
  rtk git diff --check
  rtk rg -n "Bearer [A-Za-z0-9._-]+|api[_-]?key[=:][^* ]|password[=:][^* ]" README.md outputs docs
  ```

  Expected: `git diff --check` succeeds and the secret scan finds no newly introduced credential value.

- [ ] **Step 4: Review the final diff and repository status**

  Run:

  ```bash
  rtk git diff --stat
  rtk git diff -- README.md outputs docs
  rtk git status --short
  ```

  Expected: only task-scoped Markdown files are modified; no runtime resource or infrastructure configuration changes.

- [ ] **Step 5: Live verification and cleanup**

  No live Kubernetes or external service change is required for a documentation-only revision. Confirm no temporary file or test resource was created. Proposed commit boundary: one documentation commit, `docs: revise PostOps Memory as a human-led copilot`.
