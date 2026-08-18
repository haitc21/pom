# HolmesGPT and AIC Memory Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Story/Task ID:** POSTOPS-EVAL-001

**Goal:** Build a reproducible, safely isolated Kubernetes incident evaluation suite that compares HolmesGPT alone against HolmesGPT with local AIC Memory using paired cases and a fixed scoring rubric.

**Architecture:** Declarative case files drive setup, fault injection, oracle collection, HolmesGPT requests, recovery, and cleanup. Raw JSONL results remain immutable; deterministic scoring and blinded human review generate comparison reports. Tier 0–2 run in disposable namespaces, while explicitly approved Tier 3 cases affect only one worker with snapshot and automatic rollback.

**Tech Stack:** Kubernetes v1.35.7, Calico, containerd, Helm, HolmesGPT 0.39.0 HTTP API, Prometheus, Loki, LiteLLM, PostgreSQL, Mem0 OSS, FastEmbed, Qdrant embedded, Bash, Python 3.12, JSON Schema, PyYAML, pytest.

**Spec:** `docs/testing/holmesgpt-memory-evaluation.md`

## Global Constraints

- HolmesGPT remains read-only; the harness performs setup, injection, recovery, and cleanup.
- Redmine is out of scope.
- Never commit secrets, API keys, raw credentials, full operational logs, or unredacted tool payloads.
- Pin container images by digest after validating upstream source, architecture, and license.
- Use namespace `holmes-eval-<case-id>-<run-id>` and labels `postops.poc/test`, `postops.poc/case-id`, and `postops.poc/run-id`.
- No control-plane, etcd, global Calico, NFS/PostgreSQL, monitoring, HolmesGPT, LiteLLM, or load-balancer fault injection.
- Run B must keep the same model, decoding parameters, prompt, cluster state, and case oracle as Run A.
- Use coordinated KVM snapshots of all five PoC VMs as the campaign rollback point; take an extra snapshot of the affected worker before each Tier 3 case.
- Every behavior change follows RED → observed expected failure → minimal GREEN → refactor.
- Stop immediately if cleanup or post-case infrastructure verification fails.

## Scope and blast radius

Create only `tests/holmesgpt/`, `scripts/holmes-eval/`, `docs/runbooks/holmesgpt-evaluation.md`, and a `results/holmesgpt/` ignore rule. Existing deploy manifests are consumed read-only. Kubernetes blast radius is limited to disposable namespaces for Tier 0–2; Tier 3 may stop kubelet or add one tagged reversible network rule on `k8s03` only after explicit approval.

No `.codegraph/` directory exists, so CodeGraph has no indexed blast-radius data. The implementation worker must recheck before starting.

## Contract/version decision

- Case contract version: `postops.dev/holmes-eval/v1alpha1`.
- Result record version: `postops.dev/holmes-result/v1alpha1` in append-only JSONL.
- HolmesGPT contract: `POST http://holmesgpt.k8s.local/api/chat` with a pinned model name.
- Memory contract: PostgreSQL stores engineer-approved resolutions; Mem0 indexes them with `user_id`, `agent_id`, `run_id`, `case_id`, `resolution_id`, `approval_status`, provenance, and content hash.
- Breaking schema changes require a new contract version; adding optional fields remains backward compatible.

## Threat and security scope

- Validate case IDs, paths, namespaces, resource names, and timeout ranges before passing them to shell or Kubernetes.
- Do not execute commands returned by HolmesGPT.
- Redact Kubernetes Secret data, authorization headers, LiteLLM keys, private IP metadata not needed for scoring, and raw logs beyond selected evidence.
- Prevent namespace escape and arbitrary manifest paths.
- Keep Mem0 users, agents, and runs isolated; include PostgreSQL provenance in every approved memory record.
- Secret-scan the diff and generated runbook before completion.

## Proposed commit boundaries

1. `test: define HolmesGPT evaluation contracts and controls`
2. `feat: add safe incident harness and CKAD cases`
3. `feat: add AIC Memory paired evaluation`
4. `test: add controlled CKA scenarios and reporting`
5. `docs: add HolmesGPT evaluation runbook`

No Git mutation is authorized by this plan.

---

### Task 1: Define and validate the case/result contracts

**Files:**
- Create: `tests/holmesgpt/schema/case.schema.json`
- Create: `tests/holmesgpt/schema/result.schema.json`
- Create: `tests/holmesgpt/rubric/rubric.yaml`
- Create: `tests/holmesgpt/test_schema.py`
- Create: `tests/holmesgpt/fixtures/invalid-case.yaml`
- Create: `tests/holmesgpt/fixtures/valid-case.yaml`

**Interfaces:**
- Consumes: design contract in `docs/testing/holmesgpt-memory-evaluation.md`.
- Produces: `validate_case(path) -> dict`, validated case YAML, result JSONL schema, and the fixed 100-point rubric.

- [ ] Write RED schema tests proving a valid case is accepted and missing `root_cause`, unsafe namespace text, unknown contract version, timeout above 900 seconds, or a path outside the case directory is rejected.
- [ ] Run `rtk pytest tests/holmesgpt/test_schema.py -q`; expect failures because schemas and validator do not exist.
- [ ] Implement JSON Schemas and the smallest Python validator needed for GREEN.
- [ ] Rerun the focused test and record PASS output.
- [ ] Refactor repeated fixtures without changing validation behavior.
- [ ] Run `rtk python -m json.tool tests/holmesgpt/schema/case.schema.json >/dev/null` and the equivalent result-schema check.
- [ ] Review contract compatibility against `v1alpha1` and document any optional fields.

### Task 2: Build safe preflight, lifecycle, and cleanup primitives

**Files:**
- Create: `scripts/holmes-eval/lib.sh`
- Create: `scripts/holmes-eval/preflight.sh`
- Create: `scripts/holmes-eval/run-case.sh`
- Create: `scripts/holmes-eval/cleanup.sh`
- Create: `tests/holmesgpt/test_harness.py`

**Interfaces:**
- Consumes: validated case dictionary and exact test root.
- Produces: `run-case.sh <case-file> <mode> <seed>`, a unique namespace, lifecycle timestamps, and a cleanup ledger.

- [ ] Write RED tests using a fake `kubectl` that verify rejection of namespace escape, unlabelled resources, a second active case, failed preflight, and cleanup outside the exact namespace.
- [ ] Run `rtk pytest tests/holmesgpt/test_harness.py -q`; expect failures because scripts do not exist.
- [ ] Implement preflight for three Ready nodes, healthy HolmesGPT LB endpoint, Prometheus, Loki, NFS StorageClass, and no previous dirty test namespace.
- [ ] Implement lifecycle states `CREATED`, `INJECTED`, `OBSERVED`, `RECOVERED`, `CLEANED`, and `FAILED` in a local state file.
- [ ] Implement cleanup by exact namespace plus labels; reject empty or wildcard targets.
- [ ] Rerun focused tests and shell lint; expect PASS.
- [ ] Execute a live no-fault smoke case and prove namespace deletion and unchanged infrastructure health.

### Task 3: Capture ground truth independently of HolmesGPT

**Files:**
- Create: `scripts/holmes-eval/collect-oracle.sh`
- Create: `tests/holmesgpt/test_oracle.py`
- Create: `tests/holmesgpt/fixtures/oracle-snapshots/`

**Interfaces:**
- Consumes: namespace, case ID, required evidence selectors.
- Produces: redacted `oracle.json` containing workload state, selected events, EndpointSlices, metrics queries, Loki queries, and environment health.

- [ ] Write RED tests proving Secret values and authorization headers are removed, timestamps are normalized, and missing required evidence marks the case invalid rather than silently passing.
- [ ] Run `rtk pytest tests/holmesgpt/test_oracle.py -q`; observe the expected missing implementation failure.
- [ ] Implement bounded evidence collection with explicit line/sample limits and query windows.
- [ ] Add evidence hashes so raw oracle files are immutable and auditable.
- [ ] Rerun focused tests, then collect a live healthy control oracle.
- [ ] Set `eval_oracle_file="results/holmesgpt/poc-v1-smoke/oracle.json"`, assert that exact file exists, then confirm it contains no secret values with `rtk rg -n -i 'api[_-]?key|authorization:|client-key-data|password:' "$eval_oracle_file"`.

### Task 4: Implement the first five cases and prove repeatability

**Files:**
- Create: `tests/holmesgpt/cases/control/CTRL-001.yaml`
- Create: `tests/holmesgpt/cases/lifecycle/CKAD-LIFE-001.yaml`
- Create: `tests/holmesgpt/cases/lifecycle/CKAD-LIFE-002.yaml`
- Create: `tests/holmesgpt/cases/lifecycle/CKAD-LIFE-005.yaml`
- Create: `tests/holmesgpt/cases/network/CKAD-NET-001.yaml`
- Create: `tests/holmesgpt/manifests/CTRL-001/{setup,inject,recover}/`
- Create: `tests/holmesgpt/manifests/CKAD-LIFE-001/{setup,inject,recover}/`
- Create: `tests/holmesgpt/manifests/CKAD-LIFE-002/{setup,inject,recover}/`
- Create: `tests/holmesgpt/manifests/CKAD-LIFE-005/{setup,inject,recover}/`
- Create: `tests/holmesgpt/manifests/CKAD-NET-001/{setup,inject,recover}/`
- Create: `tests/holmesgpt/test_cases.py`

**Interfaces:**
- Consumes: harness and oracle contracts.
- Produces: healthy control, CrashLoopBackOff, ImagePullBackOff, OOMKilled, and empty-EndpointSlice incidents.

- [ ] Write RED static tests for pinned API versions, required labels, one declared fault, recovery assertions, and prohibited cluster-scoped resources.
- [ ] Run `rtk pytest tests/holmesgpt/test_cases.py -q`; observe missing manifests.
- [ ] Adapt LFD259 `s_08/brokenapp.yaml`, `s_08/brokendeploy.yaml`, and `s_04/edited-stress.yaml`; replace deprecated APIs, eliminate destructive commands, and record provenance.
- [ ] Pin validated images by digest and implement minimal manifests.
- [ ] Run each case three times without HolmesGPT; require the same oracle root cause and successful cleanup every time.
- [ ] Refactor shared base manifests only after repeatability passes.
- [ ] Record live evidence that all production PoC pods and nodes remain healthy.

### Task 5: Add remaining Tier 1 CKAD cases

**Files:**
- Create: case YAML/manifests under `tests/holmesgpt/cases/{lifecycle,scheduling,configuration,security,network,storage,stateful,logging}/`
- Modify: `tests/holmesgpt/test_cases.py`

**Interfaces:**
- Consumes: stable harness/oracle and case schema.
- Produces: all Tier 1 cases listed in the design spec.

- [ ] Add a failing parameterized test enumerating every required Tier 1 case ID and expected oracle evidence.
- [ ] Run the focused test and observe missing-case failures.
- [ ] Implement cases in batches of no more than four: probes; scheduling; ConfigMap/Secret/args/RBAC; Service/DNS/NetworkPolicy/Ingress; PVC/StatefulSet/logging.
- [ ] After each batch, run three injection/recovery cycles and verify exact failure signatures.
- [ ] Reject any case whose symptom is not reliably visible to HolmesGPT's enabled toolsets.
- [ ] Run all Tier 0–1 static and live tests.

### Task 6: Capture HolmesGPT baseline requests and traces

**Files:**
- Create: `tests/holmesgpt/prompts/investigation.vi.txt`
- Create: `scripts/holmes-eval/ask-holmes.sh`
- Create: `tests/holmesgpt/test_holmes_client.py`

**Interfaces:**
- Consumes: case prompt, namespace, fixed model/config, run ID.
- Produces: one append-only result record with response, tool trace, latency, token usage, timeout status, and oracle hash.

- [ ] Write RED tests for HTTP errors, malformed JSON, timeout, missing tool trace, accidental retry, and response redaction.
- [ ] Run focused tests and observe expected failures.
- [ ] Implement exactly one HolmesGPT request per case with no human hint or hidden answer text.
- [ ] Store model and configuration fingerprints with every result.
- [ ] Run `CTRL-001` live and verify a healthy control is not diagnosed as broken.
- [ ] Run the five initial baseline cases with a recorded seed and validate JSONL against the result schema.

### Task 7: Implement deterministic and blinded scoring

**Files:**
- Create: `scripts/holmes-eval/score.py`
- Create: `scripts/holmes-eval/report.py`
- Create: `tests/holmesgpt/test_scoring.py`
- Create: `tests/holmesgpt/fixtures/responses/`

**Interfaces:**
- Consumes: result JSONL, oracle JSON, rubric YAML, optional two-reviewer CSV.
- Produces: per-case scores, paired deltas, cohort aggregates, confidence intervals, and reviewer disagreement report.

- [ ] Write RED tests for full-credit, confidently wrong RCA, hallucinated evidence, dangerous remediation, stale evidence, and score clamping.
- [ ] Run focused tests and observe missing scorer failures.
- [ ] Implement deterministic keyword/field checks only for machine-verifiable facts; leave semantic judgment fields for blinded reviewers.
- [ ] Implement anonymous response export that removes run mode and memory metadata.
- [ ] Implement paired Run B minus Run A statistics, bootstrap confidence intervals, and cohort summaries.
- [ ] Rerun scoring tests and manually inspect one generated report.

### Task 8: Integrate local AIC Memory without contaminating holdouts

**Files:**
- Create: `scripts/holmes-eval/memory-write.py`
- Create: `scripts/holmes-eval/memory-recall.py`
- Create: `tests/holmesgpt/fixtures/memory/`
- Create: `tests/holmesgpt/test_memory.py`

**Interfaces:**
- Consumes: engineer-approved PostgreSQL resolutions and local memory isolation identifiers.
- Produces: redacted approved memories, top-k retrieval records, and an injected context block with source/applicability metadata.

- [ ] Write RED tests for tenant/session isolation, holdout exclusion, unapproved-memory rejection, secret redaction, duplicate write idempotency, and top-k provenance.
- [ ] Run `rtk pytest tests/holmesgpt/test_memory.py -q`; observe expected failures.
- [ ] Implement asynchronous Mem0 recall/write using Python 3.12, FastEmbed multilingual embeddings, and Qdrant embedded storage under the task-specific data path.
- [ ] Use low-trust active recall before HolmesGPT, then rerank after live evidence is available; resolve every candidate to an approved PostgreSQL record and record which path supplied each memory.
- [ ] Seed only approved training records and verify exact, analogous, negative-transfer, and novel queries retrieve the expected relevance classes.
- [ ] Rerun focused tests and perform a live recall/write smoke test with disposable experiment identifiers.

### Task 9: Run paired baseline and memory campaigns

**Files:**
- Create locally: `results/holmesgpt/poc-v1/` (ignored)
- Modify: campaign manifest under `tests/holmesgpt/campaigns/poc-v1.yaml`

**Interfaces:**
- Consumes: frozen case suite, model fingerprint, seeds, memory partition map.
- Produces: three repetitions per Tier 0–2 case for Run A and Run B.

- [ ] Run preflight and archive the redacted environment fingerprint.
- [ ] Execute Run A in randomized order; stop on dirty cleanup or infrastructure degradation.
- [ ] Blind-score Run A before writing training memories.
- [ ] Write only approved training cases to Memory and verify holdouts are absent.
- [ ] Restore identical case baselines and execute Run B.
- [ ] Blind-score Run B, unblind only after scores are locked, and calculate paired deltas.
- [ ] Exercise negative-transfer and novel-holdout cases explicitly.
- [ ] Compare accuracy, latency, tool calls, token usage, safety, and retrieval quality against acceptance thresholds.

### Task 10: Add controlled Tier 2/3 cases after approval

**Files:**
- Create: compound/memory-negative case definitions and manifests.
- Create: `scripts/holmes-eval/tier3-preflight.sh`
- Create: `scripts/holmes-eval/tier3-rollback.sh`
- Create: `tests/holmesgpt/test_tier3_safety.py`

**Interfaces:**
- Consumes: explicit operator approval, coordinated KVM snapshot names, and the affected-worker snapshot name.
- Produces: compound cases and at most one controlled worker-level fault per run.

- [ ] Write RED safety tests proving Tier 3 cannot run against `k8s01`, without a verified KVM snapshot, without a tested `virsh snapshot-revert` command, or while another case is active.
- [ ] Run focused tests and observe expected refusal failures.
- [ ] Implement compound and negative-transfer cases first; prove cleanup.
- [ ] Create and inventory a coordinated snapshot set for `k8s01`, `k8s02`, `k8s03`, `k8s-storage`, and `k8s-lb`; verify snapshot state with `rtk virsh snapshot-list <vm>`.
- [ ] Test restore mechanics on a disposable snapshot before injecting a fault; do not test restore against the campaign baseline after results have begun.
- [ ] Implement only `CKA-NODE-001` initially, stopping kubelet on `k8s03` after recording its worker snapshot name and exact revert command.
- [ ] Verify HolmesGPT identifies the node/kubelet cause, trigger recovery, and prove all three nodes plus PoC services healthy.
- [ ] Decide whether the remaining Tier 3 cases add enough evaluation value before implementing them.

### Task 11: Independent review, security scan, full verification, and runbook

**Files:**
- Create: `docs/runbooks/holmesgpt-evaluation.md`
- Modify: `.gitignore` to exclude `results/holmesgpt/` and credential files
- Modify: `tests/holmesgpt/README.md`

**Interfaces:**
- Consumes: final diff, live campaign evidence, review findings.
- Produces: reproducible redacted runbook and a task-scoped commit proposal.

- [ ] Request an independent two-pass review: specification/contract first, then quality/failure behavior/security/tests/maintainability.
- [ ] Validate every finding technically; fix valid findings through RED/GREEN and request final re-review.
- [ ] Run focused pytest suites, shell lint, YAML/JSON validation, all safe live cases, and cleanup verification.
- [ ] Run the full repository gates available in the project plus format, lint, typing, diff check, and secret scan.
- [ ] Exercise negative paths: malformed case, Holmes timeout, Memory unavailable, cleanup failure, repeated run, stale memory, and restart/resume.
- [ ] Write the redacted runbook with commands, versions, campaign IDs, score summary, review closure, cleanup ledger, limitations, and proposed commit hashes.
- [ ] Verify no disposable namespaces/resources remain and all PoC nodes/services are healthy.
- [ ] Stop without staging, committing, or pushing; report proposed files and commit messages unless the user explicitly authorizes Git actions in that turn.
