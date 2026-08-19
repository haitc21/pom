# AIC Docker Compose demo runbook

This runbook records the first live Compose demonstration on the local host. It deliberately omits credentials, kubeconfig content, model responses containing telemetry, and raw command output.

## Runtime topology

- Compose project: `aic-demo`
- AIC API: `127.0.0.1:8080`
- HolmesGPT: internal Compose service `holmesgpt:5050`, image `robustadev/holmes:0.39.0`
- PostgreSQL: image `postgres:18`, named volume `aic-demo_aic_postgres_data`
- Qdrant: image `qdrant/qdrant:v1.19.0`, named volume `aic-demo_aic_qdrant_data`
- Holmes kubeconfig: ServiceAccount `holmesgpt-readonly` with ClusterRole verbs limited to `get`, `list`, `watch`
- External investigation target: Kubernetes 1.35.7, nodes `k8s01`, `k8s02`, `k8s03`
- External telemetry: Prometheus/Loki in the Kubernetes cluster; LiteLLM at the configured internal endpoint
- Kubernetes HolmesGPT deployment remains installed but is scaled to `0` during the Compose demo; no Helm release or data was deleted.

## Start

```bash
cd /home/haitc/project/pom/deploy/demo
cp .env.example .env
# Set LITELLM_API_KEY and a local HOLMES_API_KEY in .env.
K8S_CONTEXT='kubernetes-admin@kubernetes' bash scripts/export-readonly-kubeconfig.sh
docker compose up -d --build
docker compose ps
```

The real `.env` and generated `holmesgpt/kubeconfig` are ignored by Git. Never paste either into this runbook.

## Live verification performed

Observed on 2026-08-19:

1. All four Compose services were healthy. AIC `/health` returned `{"status":"ok","service":"aic-api"}`.
2. Alembic created the PostgreSQL schema `0001_initial` on first startup; a subsequent startup reused the same schema.
3. `bash deploy/demo/scripts/smoke-test.sh` completed with:

   ```json
   {"ok":true,"iterations":[1,2],"memory_references":0}
   ```

   The two iterations exercised create conversation, engineer-supplied command output and follow-up HolmesGPT investigation.
4. HolmesGPT returned HTTP 200 to AIC and executed read-only Kubernetes tool calls against the external cluster. The model route used was `mistral-3.5`.
5. The approved-memory seed inserted one resolution with metadata `approval_status=approved` and `resolution_id=demo-crashloop-approved`. A paraphrase search returned one result and one approved metadata value.
6. Kubernetes verification returned all three nodes `Ready`; the Kubernetes HolmesGPT deployment remained `0/0` as intended for the migration to Compose.
7. The generated kubeconfig passed `kubectl auth can-i get pods` and returned `no` for `create deployments`. A new post-restart chat returned `memory_references: 1` from the approved seed.

The first smoke request intentionally had no seeded memory reference. The separate seed and paraphrase check proves the Mem0/Qdrant recall path independently.

## API example

```bash
curl --fail --silent --header 'Content-Type: application/json' \
  --data '{"request_id":"01900000-0000-7000-8000-000000000021","conversation_id":null,"model":"mistral-3.5","message":"Pod checkout-api is CrashLoopBackOff in namespace demo. Investigate read-only.","context":{"cluster":"k8s-poc","namespace":"demo"},"command_outputs":[]}' \
  http://127.0.0.1:8080/api/chat
```

For a follow-up, reuse the returned `conversation_id`, choose a new UUIDv7 `request_id`, and send only the command and output that the engineer actually ran. Read-only Holmes tools may run automatically; a mutation is represented by a persisted `pending_approval` response and requires a separate engineer decision.

## Native Holmes remediation approval verification

Observed on 2026-08-19 with the disposable namespace
`holmes-eval-aic-approval-probe`:

1. Holmes emitted native `run_kubectl_command` for bounded `scale`. AIC returned `pending_approval`, immutable action details and expiry; no mutation had happened yet.
2. After the engineer submitted an approval decision, AIC resumed the signed Holmes conversation.
3. The MCP ServiceAccount executed only `scale deployment/approval-probe --replicas=2`; Kubernetes reported `2/2 Ready` and two `Running` pods.
4. A preceding empty patch was rejected and left its ConfigMap unchanged, proving the deny path.

The MCP has no Secret, RBAC, node, storage or delete permission. Its generic tool rejects shell metacharacters and JSON merge-patch payloads. Content-changing ConfigMap remediation needs a future typed MCP tool with explicit schema validation.

## Stop and preserve state

```bash
docker compose stop
```

This preserves PostgreSQL and Qdrant named volumes. Do not use `docker compose down -v` during the demo. Keep the KVM Kubernetes cluster, NFS, PostgreSQL-for-Grafana, monitoring and load balancer running because they are external dependencies for the investigation.

## Known limitations

- No authentication layer exists in front of AIC; the demo is bound to the local host port.
- Prometheus/Loki endpoint reachability from Compose depends on the current PoC NodePort/routing configuration.
- FastEmbed downloads its model on first memory operation and may contact Hugging Face; add a persistent model-cache volume before offline operation.
- No Redmine integration, UI, automated remediation, Skill approval workflow, HA or backup is included.
