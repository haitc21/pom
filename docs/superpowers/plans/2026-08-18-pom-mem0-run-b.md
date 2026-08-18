# POM-MEM0-RUN-B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run CKAD-LIFE-001 with a local Mem0 OSS memory seeded from the engineer-approved Run A resolution, inject only recalled context into HolmesGPT, and record a paired Run B result.

**Architecture:** Mem0 Python library runs on the host in a Python 3.12 venv. FastEmbed generates multilingual embeddings locally and Qdrant embedded stores vectors under `/data/k8s-poc/mem0/data`. The harness calls HolmesGPT through a temporary local port-forward and writes redacted evidence to the Run B Markdown/runbook files.

**Tech Stack:** Python 3.12, Mem0 OSS 2.0.18, FastEmbed 0.8.0, Qdrant client 1.19.0, LiteLLM-backed HolmesGPT 0.39.0, Kubernetes 1.35.7.

**Spec:** `docs/testing/holmesgpt-memory-evaluation.md` and `outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md`

## Global Constraints

- No external managed memory service dependency is used.
- PostgreSQL business-database integration is not implemented in this first memory spike; Run A Markdown is the approved seed source.
- Mem0 is used only for recall; Run A's engineer-confirmed resolution is inserted with `infer=False`.
- HolmesGPT remains read-only; no command returned by the model is executed.
- API keys remain in environment variables and never enter source, results, or logs.
- The Run B test uses the same CKAD-LIFE-001 oracle and prompt intent as Run A.
- Qdrant/Mem0 data is disposable PoC data under `/data/k8s-poc/mem0/data`.

---

### Task 1: Write and observe failing harness tests

**Files:**
- Create: `scripts/holmes-eval/memory_run_b.py`
- Create: `tests/holmesgpt/test_memory_run_b.py`

- [x] Write tests for deterministic resolution-document creation, prompt injection, and response redaction.
- [x] Run `rtk python3.12 -m unittest tests/holmesgpt/test_memory_run_b.py -v`; observed the expected import failure before implementation.

### Task 2: Implement the minimal local Mem0/HolmesGPT harness

**Files:**
- Modify: `scripts/holmes-eval/memory_run_b.py`
- Create: `scripts/holmes-eval/requirements-mem0.txt`

- [x] Implement `build_resolution_document`, `build_memory_prompt`, and `redact_response`.
- [x] Implement host-side Mem0 initialization with FastEmbed/Qdrant paths supplied by arguments.
- [x] Seed only the approved Run A resolution with `infer=False`, search with scoped metadata, and return memory ID/score.
- [x] Implement HolmesGPT POST through an injected base URL and model without executing returned commands.
- [x] Rerun focused tests and verify GREEN.

### Task 3: Install the disposable local runtime and run Run B

**Files:**
- Create/update: `/data/k8s-poc/mem0/venv` (runtime only; not tracked)
- Create/update: `/data/k8s-poc/mem0/data` (runtime only; not tracked)
- Modify: `docs/testing/holmesgpt/CKAD-LIFE-001/run-b-holmesgpt-memory.md`
- Create: `docs/runbooks/holmesgpt-evaluation-run-b-mem0.md`

- [x] Create a Python 3.12 venv under `/data/k8s-poc/mem0/venv` and install pinned requirements.
- [x] Start `kubectl -n holmesgpt port-forward svc/holmesgpt-holmes 18080:80` and verify the endpoint.
- [x] Seed and recall the approved Run A resolution, then call HolmesGPT with the same investigation intent plus a redacted memory block.
- [x] Capture request, recall score, response, timing, and oracle references without secrets.
- [x] Stop the port-forward and verify no test namespace/resource was created.

### Task 4: Score and verify the paired result

- [x] Score Run B with the existing 100-point rubric and compare against Run A's 88/100.
- [x] Record whether memory was relevant, whether it caused anchoring, and whether the response preserved namespace/image/fault provenance.
- [x] Run `git diff --check`, secret scan, and `git status --short`; no runtime data may appear in the repository.
- [ ] Propose one documentation commit; do not commit/push without explicit authorization.
