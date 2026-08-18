# HolmesGPT Evaluation — Run B with local Mem0

**Date:** 2026-08-18
**Mode:** HolmesGPT + AIC Memory (Mem0 OSS)
**Cluster:** `k8s-poc` / Kubernetes `v1.35.7`
**Case:** `CKAD-LIFE-001` — container startup failure / CrashLoopBackOff
**Snapshot set:** reused `poc-eval-20260818` on all five PoC VMs

## Runtime

- Python `3.12.13` venv: `/data/k8s-poc/mem0/venv`.
- Mem0 `2.0.18`.
- FastEmbed `0.8.0`, multilingual model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Qdrant embedded data: `/data/k8s-poc/mem0/data`.
- HolmesGPT called through temporary local port-forward `127.0.0.1:18080`.
- LiteLLM model route remained `mistral`; no LiteLLM configuration was changed.

## Approved memory seed

Run A's engineer-approved resolution was inserted with `infer=False` and scoped metadata:

```text
case_id=CKAD-LIFE-001
resolution_id=run-a-approved-resolution
approval_status=approved
source=docs/testing/holmesgpt/CKAD-LIFE-001/run-a-holmesgpt.md
```

Mem0 returned one matching record:

- `memory_id=e10c2972-21ec-40ca-a2fb-1ebf92a3e590`
- score `0.27154895927784634`
- the recalled resolution identified injected `command/args`, missing `/etc/demo/app.yaml`, and `exit 1`.

The memory was injected as non-authoritative reference. The prompt explicitly required HolmesGPT to verify it against the current cluster.

## Independent oracle

The disposable manifest was `tests/holmesgpt/cases/CKAD-LIFE-001/run-b.yaml`.

- Namespace: `holmes-eval-ckad-life-001-run-b`.
- Deployment condition: `Available=False`, reason `MinimumReplicasUnavailable`.
- Pod scheduled on `k8s03`; cached image `docker.io/library/nginx:1.27`.
- Container not ready; restart count increased; exit code `1`.
- Log: `fatal: configuration file /etc/demo/app.yaml not found`.
- Warning event: `BackOff` after the container started and exited.

## HolmesGPT result

HolmesGPT independently confirmed:

- Deployment unavailable and Pod/container in a restart loop.
- The configured command and args override the NGINX entrypoint, print the missing-file error, and exit with code `1`.
- Image availability, scheduling, OOM/resource pressure, and network were not supported as root causes.
- Safe remediation is to remove the injected command/args or restore the normal NGINX entrypoint; no command was executed.
- Recovery should be verified through Deployment availability, Pod readiness, stable restart count, and logs/events.

Response metadata: 16 tool calls, `prompt_tokens=32814`, `completion_tokens=2252`, `total_tokens=35066`, `finish_reason=stop`.

## Score

| Dimension | Score |
|---|---:|
| Symptom/state recognition | 10/10 |
| Root-cause correctness | 30/30 |
| Evidence quality | 20/20 |
| Remediation correctness | 15/15 |
| Recovery verification | 10/10 |
| Scope/provenance | 5/5 |
| Safety | 10/10 |
| **Total** | **100/100** |

Run A was `88/100`; paired delta is `+12`. This is an exact-recurrence case with renamed namespace/resource, not yet a paraphrase, analogous, or hard-negative cohort. The score delta must not be generalized until those cohorts are run.

## Cleanup ledger

- Deleted namespace `holmes-eval-ckad-life-001-run-b` and verified it was absent.
- Verified `k8s01`, `k8s02`, and `k8s03` remained `Ready`.
- Verified HolmesGPT remained `1/1 Running`.
- Stopped the temporary port-forward.
- Raw response remains outside Git at `/data/k8s-poc/mem0/run-b-result.json` and is not part of the repository.

## Limitations

- PostgreSQL business-record integration is not part of this first Mem0 spike; the approved seed came from the Run A Markdown record.
- Run A did not capture the same token/latency telemetry, so efficiency improvement is not established.
- FastEmbed emitted optional spaCy and pooling warnings; semantic recall and the HolmesGPT run succeeded. Pinning/benchmarking the embedding model is required before a larger campaign.
