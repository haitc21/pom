# HolmesGPT Remaining Test Campaign

## Scope

- Run all remaining Tier 0–3 workload, memory, node, network, and DNS cases from `docs/testing/holmesgpt-memory-evaluation.md`.
- Every case gets isolated Run A and Run B namespaces, raw responses outside Git, per-run Markdown, and a case `README.md`.
- Run B uses only an approved resolution seed and records recall provenance.
- Tier 3 CKA/node cases are included after a fresh snapshot of `k8s01`, `k8s02`, `k8s03`, `k8s-lb`, and `k8s-storage`; rollback is the required recovery path for each node/network fault.

## Acceptance

- [ ] Case manifests/oracles are generated only for disposable namespaces with `postops.poc/case-id` labels, or explicitly labelled reversible VM/node faults.
- [ ] Run A and Run B use the same prompt intent and model configuration.
- [ ] Each case records score, duration, tool calls, token usage, memory recall, limitations, and cleanup evidence.
- [ ] Each namespace is absent after its case and all PoC nodes/services remain healthy.
- [ ] Summary table contains one row per executed case and explicitly marks skipped Tier 3 cases.
- [ ] No credentials or raw provider responses are committed.

## Execution gates

1. RED: validate the batch case schema and reject missing oracle/evidence fields.
2. GREEN: run safe workload cases sequentially with timeout and cleanup traps.
3. Review output for false positives, stale-memory anchoring, and fabricated evidence.
4. Run unit tests, diff/secret checks, and cluster health verification.

## Proposed implementation files

- `scripts/holmes_eval/batch_remaining.py`
- `tests/holmesgpt/test_batch_remaining.py`
- `tests/holmesgpt/cases/<CASE-ID>/run-a.yaml`
- `tests/holmesgpt/cases/<CASE-ID>/run-b.yaml`
- `docs/testing/holmesgpt/<CASE-ID>/README.md`
- `docs/testing/holmesgpt/<CASE-ID>/run-a-holmesgpt.md`
- `docs/testing/holmesgpt/<CASE-ID>/run-b-holmesgpt-memory.md`
- `docs/testing/holmesgpt/README.md`

## Cleanup and handoff

- Delete only namespaces created by the batch runner.
- Record snapshot IDs before Tier 3 and rollback IDs after any failed node/network case.
- Verify `kubectl get nodes`, HolmesGPT, Prometheus, Loki, Grafana, and the NFS/PostgreSQL VM are unchanged.
- Do not commit or push without an explicit Git request in the task that produces the final verified diff.
