# HolmesGPT Kubernetes Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy HolmesGPT as a read-only HTTP service in the existing Kubernetes PoC, connected to LiteLLM, Prometheus, and Loki without Redmine or remediation actions.

**Architecture:** HolmesGPT runs in namespace `holmesgpt` using the official Robusta Helm chart. Its ServiceAccount receives only read permissions for Kubernetes and monitoring resources. Prometheus and Loki are accessed through cluster DNS; the OpenAI-compatible LiteLLM endpoint is supplied through a Kubernetes Secret and model list. The API is exposed internally first and validated with port-forward; external ingress is deferred until the API is proven.

**Tech Stack:** Kubernetes v1.35.7, Helm, HolmesGPT Helm chart, containerd, Calico, kube-prometheus-stack Prometheus, Loki gateway, external LiteLLM OpenAI-compatible API.

---

### Task 1: Prepare reproducible HolmesGPT configuration

**Files:**
- Create: `docs/superpowers/plans/2026-08-17-holmesgpt-k8s-deployment.md`
- Create (local disposable): `/tmp/holmesgpt-values.yaml`
- Create (cluster secret): `holmesgpt-secrets` in namespace `holmesgpt`; secret data never committed

- [ ] **Step 1: Verify source endpoints without exposing credentials**

Run:

```bash
curl --max-time 10 -o /dev/null -w '%{http_code}\n' \\
  -H "Authorization: Bearer $LITELLM_API_KEY" \\
  https://llmpipe.vnpost.vn/v1/models
```

Expected: HTTP 200 from the host; do not print the response body or API key.

- [ ] **Step 2: Create namespace and Secret from `/home/haitc/project/LibreChat/.env`**

Extract `LITELLM_API_KEY` in a shell without committing it, create namespace `holmesgpt`, and create Secret `holmesgpt-secrets` with key `LITELLM_API_KEY`. Verify only the key exists and never display its value.

- [ ] **Step 3: Write Helm values with read-only integrations**

Use these exact service URLs:

```yaml
modelList:
  litellm:
    api_key: "{{ env.LITELLM_API_KEY }}"
    model: openai/<MODEL_NAME>
    api_base: "https://llmpipe.vnpost.vn/v1"
    temperature: 0
additionalEnvVars:
  - name: LITELLM_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: LITELLM_API_KEY
toolsets:
  kubernetes/core:
    enabled: true
  kubernetes/logs:
    enabled: true
  kubernetes/kube-prometheus-stack:
    enabled: true
  prometheus/metrics:
    enabled: true
    subtype: prometheus
    config:
      prometheus_url: http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090
  loki/logs:
    enabled: true
    config:
      loki_url: http://loki-gateway.loki.svc.cluster.local
```

The actual LiteLLM model name must be read from `/v1/models`; no guessed model may be used. Do not enable Kubernetes Remediation/MCP or any write-capable toolset.

### Task 2: Validate chart and cluster egress before installation

**Files:**
- Modify: `/tmp/holmesgpt-values.yaml`

- [ ] **Step 1: Add the official chart and render locally**

Run:

```bash
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update
helm template holmesgpt robusta/holmes -n holmesgpt -f /tmp/holmesgpt-values.yaml > /tmp/holmesgpt-rendered.yaml
```

Expected: render succeeds; inspect that the ServiceAccount, ClusterRole, Secret references, model list, and disabled remediation settings are present.

- [ ] **Step 2: Test cluster-to-LiteLLM network path**

Run a disposable curl pod in `holmesgpt` using an image already cached in the cluster, or attach temporary bootstrap NAT only if no cached curl image exists. Call `/v1/models` with the Secret injected and report only HTTP status. Expected: HTTP 200. If it fails because `postops-k8s` intentionally has no egress, stop before Helm install and request an approved egress design (internal proxy or controlled NAT).

- [ ] **Step 3: Verify in-cluster Prometheus and Loki endpoints**

From a disposable pod, request Prometheus `/api/v1/status/buildinfo` and Loki `/ready`. Expected: HTTP 200; retain no test pod or credentials.

### Task 3: Install HolmesGPT with least-privilege access

**Files:**
- Modify: `docs/infra/k8s.md` with the final Helm command, namespace, service, toolsets, and verification results
- Cluster resources: Helm release `holmesgpt` in namespace `holmesgpt`

- [ ] **Step 1: Install the official chart**

Run:

```bash
helm upgrade --install holmesgpt robusta/holmes \\
  --namespace holmesgpt --create-namespace \\
  --values /tmp/holmesgpt-values.yaml \\
  --wait --timeout 5m
```

Expected: Deployment available and Service present. The Helm chart's generated ClusterRole must be reviewed before acceptance; remove any write verbs not required by enabled read-only toolsets.

- [ ] **Step 2: Confirm pod and RBAC state**

Run:

```bash
kubectl -n holmesgpt get pods,svc
kubectl -n holmesgpt auth can-i --as=system:serviceaccount:holmesgpt:holmesgpt get pods --all-namespaces
kubectl -n holmesgpt auth can-i --as=system:serviceaccount:holmesgpt:holmesgpt delete pods --all-namespaces
```

Expected: pod Running, read check `yes`, delete check `no`. Use the actual ServiceAccount name from the rendered chart if it differs.

### Task 4: Verify API and toolsets

**Files:**
- Modify: `docs/infra/k8s.md` with fresh command output summaries and limitations

- [ ] **Step 1: Port-forward the service**

```bash
kubectl -n holmesgpt port-forward svc/holmesgpt-holmes 18080:80
```

- [ ] **Step 2: Check health and API authentication**

Call the documented health endpoint and `/api/chat` with the configured model name and an API key if chart auth is enabled. Expected: health succeeds; chat returns a non-empty response without leaking the LiteLLM key.

- [ ] **Step 3: Exercise read-only investigations**

Run three acceptance prompts: list cluster nodes, inspect a known monitoring pod, and query a recent Prometheus metric. A Loki query is required if the Loki toolset is enabled. Record HTTP status, tool names used, and summarized result; do not store raw secrets or full log payloads.

- [ ] **Step 4: Exercise negative permissions**

Attempt a remediation-like request such as deleting a disposable pod. Expected: HolmesGPT refuses or Kubernetes RBAC denies the action. No real workload may be changed.

### Task 5: Cleanup, documentation, and completion gates

**Files:**
- Modify: `docs/infra/k8s.md`
- Create: `docs/runbooks/holmesgpt-k8s.md` with redacted commands, verification summaries, limitations, and cleanup ledger

- [ ] **Step 1: Remove disposable test pods and temporary files**

Delete only resources created for connectivity/negative tests. Keep the HolmesGPT release, namespace, Secret, and configuration. Remove local rendered values containing no credentials; securely clear any temporary kubeconfig or credential-bearing files.

- [ ] **Step 2: Run final gates**

Run `helm status`, `kubectl get pods`, `kubectl get events --sort-by=.lastTimestamp`, API health, read-only prompt tests, negative RBAC test, and `git diff --check`. Expected: all required pods Ready, no unresolved warning events, API usable, write access denied.

- [ ] **Step 3: Review and commit only task-scoped documentation**

Proposed commit: `feat: deploy HolmesGPT read-only Kubernetes integration`. Do not commit Secrets, API keys, kubeconfigs, rendered manifests containing credentials, or raw provider responses.
