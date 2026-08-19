# AIC Docker Compose demo

This stack runs the AI Incident Copilot API, PostgreSQL 18 business storage, Mem0/Qdrant memory and HolmesGPT. Kubernetes, Prometheus, Loki, NFS and LiteLLM remain external dependencies; the existing Kubernetes HolmesGPT deployment is scaled to zero while this demo is active.

## Start

```bash
cd deploy/demo
cp .env.example .env
# Edit .env and set LITELLM_API_KEY.
kubectl apply -f holmesgpt/readonly-rbac.yaml
bash scripts/export-readonly-kubeconfig.sh
docker compose up -d --build
docker compose ps
```

The API is published at `http://127.0.0.1:${AIC_PORT:-8080}`. A conversation is created with `POST /api/chat`; subsequent requests use the returned `conversation_id` and include command output collected by the engineer. Read-only Holmes tools run automatically. A mutating MCP call is persisted by AIC and can run only after a separate engineer decision.

## API endpoints

OpenAPI/Swagger UI is available at `http://127.0.0.1:8080/docs`.

- `GET /health` — service and PostgreSQL health check.
- `POST /api/chat` — create a conversation or append an investigation iteration.
- `GET /api/conversations/{conversation_id}` — conversation metadata and accumulated context.
- `GET /api/conversations/{conversation_id}/messages` — persisted user/assistant history.
- `GET /api/requests/{request_id}` — idempotency record and completed response for one request.
- `POST /api/conversations/{conversation_id}/resolution` — lưu kết luận đã được kỹ sư xác nhận vào PostgreSQL và Mem0/Qdrant.
- `GET /api/approvals/{approval_id}` — đọc action Holmes đang chờ kỹ sư xác nhận.
- `POST /api/approvals/{approval_id}/decision` — approve/reject toàn bộ action đang chờ, có audit người duyệt.

Example lookups after `POST /api/chat` returns a conversation and request ID:

```bash
curl -sS "http://127.0.0.1:8080/api/conversations/$CONVERSATION_ID" | jq
curl -sS "http://127.0.0.1:8080/api/conversations/$CONVERSATION_ID/messages" | jq
curl -sS "http://127.0.0.1:8080/api/requests/$REQUEST_ID" | jq
```

## Kubernetes remediation với engineer approval

Read-only investigation vẫn chạy tự động. AIC không tự chạy action có thay đổi.
Khi Holmes gọi remediation tool, `POST /api/chat` trả `status: pending_approval`,
gồm `approval_id` và danh sách action. Mỗi action chỉ chạy sau khi kỹ sư gửi một
quyết định cho mọi `tool_call_id` đang chờ:

```bash
curl -sS -X POST "http://127.0.0.1:8080/api/approvals/$APPROVAL_ID/decision" \
  -H 'Content-Type: application/json' \
  -d '{
    "approved_by": "devops-engineer",
    "decisions": [
      {"tool_call_id": "call_123", "approved": true}
    ]
  }' | jq
```

The decision is persisted with the action description and final Holmes response.
Rejecting any action rejects the approval batch and does not resume Holmes.

Apply the remediation MCP resources only once:

```bash
docker build -t aic-kubernetes-remediation-mcp:1.1.0-poc \
  holmesgpt/remediation-mcp
kubectl apply -f holmesgpt/remediation-mcp.yaml
kubectl -n holmes-mcp rollout status deployment/k8s-remediation-mcp-server
```

The executor is intentionally scoped: it can patch/scale/rollout selected
workloads and ConfigMaps, but cannot access Secrets, RBAC, storage, nodes or
delete resources. Only after the MCP pod is healthy should remediation be
enabled in `deploy/demo/.env`:

```bash
HOLMES_TOOLSET_CONFIG=/etc/holmes/config/remediation-toolset.yaml
docker compose --env-file .env up -d --force-recreate holmesgpt
```

The Compose container cannot resolve Kubernetes `*.svc.cluster.local` names.
For this PoC the MCP Service is therefore a NodePort reachable only on the KVM
NAT network (`10.77.0.12:30800`), configured in
`holmesgpt/remediation-toolset.yaml`. Do not expose it on a public interface.

The generic `run_kubectl_command` tool deliberately rejects shell
metacharacters and JSON merge-patch arguments. It is appropriate for bounded
operations such as `scale` and `rollout restart`. Add a typed, schema-validated
MCP operation before allowing ConfigMap content changes; do not weaken the
argument validator merely to permit arbitrary patches.

If the MCP image cannot be pulled, leave this variable unset. Holmes and AIC
remain in read-only mode; a missing remediation executor must never block an
investigation.

Engineer approval is explicit; only `approval_status=approved` records are indexed into memory:

```bash
curl -sS -X POST "http://127.0.0.1:8080/api/conversations/$CONVERSATION_ID/resolution" \
  -H 'Content-Type: application/json' \
  -d '{
    "resolution_id": "incident-2026-001-v1",
    "approved_by": "devops-engineer",
    "summary": "Concise engineer-confirmed resolution",
    "evidence": ["verbatim evidence 1", "verbatim evidence 2"],
    "confirmed_facts": ["fact proven by evidence"],
    "unconfirmed_hypotheses": ["hypothesis not proven"],
    "approval_status": "approved"
  }' | jq
```

## Seed memory and smoke test

```bash
set -a; source .env; set +a
docker compose exec -T aic-api python /opt/aic/seed-approved-resolution.py
bash scripts/smoke-test.sh
```

The API owns approval checks and persistence. The smoke test verifies two iterations and prints only redacted metadata.

## Memory safety policy

AIC treats approved memory as historical investigation guidance, never as evidence
for the current incident:

- Iteration 1 does not retrieve memory.
- Later iterations retrieve memory only after current command output provides a
  recognizable incident signature.
- Candidates must be approved, meet `MEM0_MIN_SCORE`, and match the structured
  `incident_type`, `failure_reason`, and `resource_kind` metadata supplied with
  the approved resolution.
- HolmesGPT must re-verify historical facts using current Kubernetes or engineer
  command output before using them in a conclusion.

When approving a resolution, populate the optional signature fields whenever
they are known, for example:

```json
{
  "incident_type": "image_pull_failure",
  "failure_reason": "ImagePullBackOff",
  "resource_kind": "Pod"
}
```

## Stop and preserve data

```bash
docker compose stop
```

Do not use `docker compose down -v`; named PostgreSQL and Qdrant volumes are the demo's persistent state. Keep the Kubernetes cluster running because HolmesGPT uses it as the investigation target.
