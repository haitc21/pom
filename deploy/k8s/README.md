# HolmesGPT PoC deployment artefacts

These files describe the current single-node/single-replica PoC configuration. They are Helm values, not standalone rendered manifests; install the pinned chart versions shown below.

## Prerequisites

- Kubernetes 1.35.x, Calico, and containerd.
- `nfs-client` StorageClass backed by `k8s-storage` for Loki (and the existing Alertmanager/Prometheus claims).
- PostgreSQL on `10.77.0.14` with database `grafana` and user `grafana`.
- The host route/`hostAliases` required for the private LiteLLM endpoint, as described in `docs/infra/k8s.md`.

## Install order

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add robusta https://robustadev.github.io/holmes
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace holmesgpt --dry-run=client -o yaml | kubectl apply -f -

# Create the runtime-only secrets from the *.example.yaml templates first.
kubectl -n monitoring apply -f secrets/grafana-admin.example.yaml
kubectl -n monitoring apply -f secrets/grafana-postgres.example.yaml
kubectl -n holmesgpt apply -f secrets/holmesgpt.example.yaml

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --version 88.3.0 -f values/monitoring.yaml --wait
helm upgrade --install loki grafana/loki \
  --namespace loki --version 18.9.0 -f values/loki.yaml --wait
helm upgrade --install holmesgpt robusta/holmes \
  --namespace holmesgpt --version 0.39.0 -f values/holmesgpt.yaml --wait

# Required only while LiteLLM is reached through the current lab route.
kubectl apply -f holmesgpt-hostaliases.patch.yaml
kubectl apply -f holmesgpt-ingress.yaml
```

Add `10.77.0.15 holmesgpt.k8s.local` to the host's `/etc/hosts`. The existing
`k8s-lb` default HTTP virtual host forwards unmatched hosts to ingress-nginx
NodePort `30553`, so no separate HolmesGPT NodePort is required.

Verify with `kubectl get nodes` and `kubectl -n holmesgpt rollout status deploy/holmesgpt-holmes`.
