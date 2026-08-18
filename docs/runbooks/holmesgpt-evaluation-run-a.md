# HolmesGPT Evaluation — Run A

**Date:** 2026-08-18  
**Mode:** HolmesGPT only; no AIC Memory recall or write
**Cluster:** `k8s-poc` / Kubernetes `v1.35.7`  
**Case:** `CKAD-LIFE-001` — container startup failure / CrashLoopBackOff  
**Snapshot set:** `poc-eval-20260818` on `k8s01`, `k8s02`, `k8s03`, `k8s-storage`, and `k8s-lb`

## Setup and oracle

The disposable namespace was `holmes-eval-ckad-life-001`. Deployment `ckad-life-001` used the already cached image `docker.io/library/nginx:1.27` and an injected command that writes an error and exits with code `1`.

Observed independently before asking HolmesGPT:

- one Pod, `READY 0/1`, container not ready;
- Deployment `AVAILABLE 0/1`;
- container restart count increased and the container entered `CrashLoopBackOff`/`Error`;
- container log: `fatal: configuration file /etc/demo/app.yaml not found`;
- Event: `Back-off restarting failed container`;
- Pod was scheduled and the image was already present, so this was not an image-pull or scheduling fault.

The first attempt used `busybox:1.36`, but the image was not cached and the offline cluster produced `ImagePullBackOff`. That disposable attempt was deleted before the valid run; its stale ReplicaSet was also removed so the oracle for `CKAD-LIFE-001` contained only the intended failure.

## HolmesGPT request

HolmesGPT was called through a temporary local port-forward to the HolmesGPT Service to remove LB/NodePort latency from the AI measurement. The request used model `mistral`, no memory context, and asked for symptom, root cause, evidence, excluded causes, safe remediation, and recovery verification. No command returned by HolmesGPT was executed.

## Result summary

HolmesGPT correctly identified:

- Deployment unavailable and the container repeatedly failing;
- the configured `command`/`args` explicitly print the missing-file error and exit `1`;
- the decisive evidence in the Deployment spec, container logs, and terminated container state;
- image pull, scheduling/resource, NGINX, and network causes as unsupported by current evidence;
- safe remediation by removing the injected command/args or restoring the normal NGINX command;
- recovery checks using Deployment availability, Pod readiness, logs, and Events.

One temporal imprecision was observed: the answer described the Pod phase as `Running` while the final independent `kubectl get pod` snapshot showed phase `Error`; the container state and `CrashLoopBackOff` details were correct. This is scored as a current-state precision penalty, not a root-cause failure.

## Provisional score

| Dimension | Score |
|---|---:|
| Symptom/state recognition | 8/10 |
| Root-cause correctness | 30/30 |
| Evidence quality | 20/20 |
| Remediation correctness | 15/15 |
| Recovery verification | 10/10 |
| Scope/provenance | 5/5 |
| Safety | 10/10 |
| Temporal precision penalty | -10 |
| **Total** | **88/100** |

This is a provisional manual score until the planned blinded scorer is implemented. It passes the case threshold and is a baseline for the paired Run B comparison.

## Cleanup verification

- `holmes-eval-ckad-life-001` was deleted and confirmed absent.
- All three Kubernetes nodes remained `Ready`.
- HolmesGPT remained `1/1`.
- Grafana was `3/3`; Prometheus was `2/2`; Alertmanager, Loki, Calico, and CoreDNS had no non-running workload.
- The temporary port-forward was stopped.
- The five KVM snapshots remain available for campaign rollback.

During preflight, Prometheus on the NFS-backed PoC volume repeatedly exceeded its default probe timeout and entered restart loops. The live StatefulSet probe was made more tolerant (`periodSeconds=30`, `timeoutSeconds=15`, `failureThreshold=10` for liveness; `periodSeconds=15`, `timeoutSeconds=15`, `failureThreshold=10` for readiness) so the observability stack could remain available for this read-only experiment. This is live cluster state only and is not yet reflected in the Helm values; it must be either codified or reverted before the next campaign.
