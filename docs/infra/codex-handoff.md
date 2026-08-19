# Codex handoff – AI Incident Copilot (AIC) PoC

Last updated: 2026-08-19

## Current objective

Validate the AI Incident Copilot (AIC) idea: use HolmesGPT for read-only Kubernetes/observability investigation, PostgreSQL for authoritative business records, and local AIC Memory for approved operational recall. Redmine integration is intentionally not implemented yet.

## PoC state

- Kubernetes 1.35.7, Calico, containerd.
- VMs: `k8s01` (10.77.0.11, control-plane), `k8s02` (.12, worker), `k8s03` (.13, worker).
- `k8s-storage` (10.77.0.14): NFS export `/srv/nfs/k8s`; PostgreSQL 16 single instance on the normal VM filesystem, database/user `grafana`.
- `k8s-lb` (10.77.0.15): Nginx forwards HTTP to ingress-nginx NodePort 30553.
- Grafana: one replica, PostgreSQL backend, no NFS SQLite.
- Loki: one monolithic replica using NFS.
- Prometheus: one replica; current PoC storage remains the existing NFS PVC.
- HolmesGPT: Helm release `holmesgpt`, chart/image 0.39.0, namespace `holmesgpt`; deployment is intentionally scaled to `0` while HolmesGPT is transitioned to Docker Compose. The Helm release and configuration remain intact.
- HolmesGPT RBAC is read-only (`get/list/watch`); delete pod is denied.
- The legacy Kubernetes endpoint `http://holmesgpt.k8s.local/api/chat` is unavailable while the deployment is scaled to `0`.
- Host CLI `holmes` 0.39.0 is installed with Python 3.12 and is a standalone agent; it is not a remote client for the HolmesGPT server. The server remains the intended PoC path.

## HolmesGPT configuration

- LiteLLM endpoint: `https://llmpipe.vnpost.vn/v1`.
- Current model alias: `mistral-3.5` → `openai/mistral-3.5`.
- Enabled: Kubernetes core/logs, kube-prometheus-stack, Prometheus metrics, Grafana Loki.
- Disabled: Internet, Bash, Robusta, Skills, Connectivity Check and write/remediation actions.
- `CLUSTER_NAME=k8s-poc` is configured.
- HolmesGPT values and secret templates: `deploy/k8s/`.
- Do not commit API keys, PostgreSQL passwords or Grafana passwords.

## Reproducible artefacts

- `deploy/k8s/README.md` – install order and pinned chart versions.
- `deploy/k8s/values/holmesgpt.yaml`
- `deploy/k8s/values/monitoring.yaml`
- `deploy/k8s/values/loki.yaml`
- `deploy/k8s/holmesgpt-ingress.yaml`
- `deploy/k8s/holmesgpt-hostaliases.patch.yaml`
- `deploy/k8s/secrets/*.example.yaml`
- Main runbook: `docs/infra/k8s.md`.

## Key validation already completed

- All three Kubernetes nodes were `Ready`.
- HolmesGPT API through the LB returned correct node status.
- HolmesGPT warnings for missing `CLUSTER_NAME` and invalid `loki/logs` were fixed; the valid built-in name is `grafana/loki` with `api_url`.
- Helm release `holmesgpt` was deployed at revision 9 before shutdown.
- Git commit pushed to `origin/main`: `052fe1a` (`Document and package HolmesGPT PoC infrastructure`).

## Startup validation — 2026-08-18

- Started `k8s01`, `k8s02`, `k8s03`, `k8s-storage`, and `k8s-lb`.
- All Kubernetes nodes are `Ready` on Kubernetes `v1.35.7`.
- Restored the storage VM's Calico Pod CIDR routes and persisted them under the existing `k8s0` Netplan interface. The previous standalone route file created a conflicting `eth1` definition and removed the storage IP after `netplan apply`.
- Restarted kube-proxy to refresh NodePort rules after the network repair.
- Grafana is `3/3` and `/api/health` through `http://10.77.0.15` returns `database: ok`.
- Prometheus, Loki, Alertmanager, Calico, CoreDNS, and HolmesGPT are running; all three nodes are Ready.
- HolmesGPT through `holmesgpt.k8s.local` answered a live query with `3 node đang Ready.`

## Next recommended work

1. Keep the five PoC VMs running and verify `kubectl get nodes` before demo work.
2. Implement the Docker Compose demo in `docs/superpowers/plans/2026-08-19-aic-docker-compose-demo.md`.
3. Verify the Compose HolmesGPT `/api/chat` endpoint against the external Kubernetes cluster.
4. Seed 10–20 approved `CrashLoopBackOff`/`OOMKilled` cases.
5. Compare baseline investigation versus `recall → investigate → feedback → write memory`.
6. Evaluate Mem0 OSS as an optional extraction/retrieval layer against direct PostgreSQL/pgvector search before committing to a production architecture.

## Credentials and sensitive files

Credentials are intentionally absent from this file and the repository. Runtime secrets remain in Kubernetes Secrets and local environment/config files only.
