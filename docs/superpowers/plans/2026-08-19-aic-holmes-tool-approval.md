# AIC HolmesGPT Tool Approval Implementation Plan

**Goal:** Enable HolmesGPT Kubernetes remediation through AIC while forcing an engineer approval before every mutating action.

**Architecture:** Holmes retains automatic read-only investigation. AIC calls the Holmes HTTP API in streaming approval mode, persists an approval request when Holmes pauses, exposes a read endpoint and an approve/reject endpoint, then resumes Holmes with the verified tool decision. Kubernetes mutations are performed only by Holmes' remediation MCP server with its scoped ServiceAccount.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL 18, HTTPX SSE, HolmesGPT 0.39, Kubernetes Remediation MCP.

## Constraints

- Never give Holmes or the MCP server `cluster-admin`.
- No `secrets` access.
- Read-only built-in Holmes tools execute without approval.
- Every MCP `run_kubectl_command` requires an explicit engineer decision.
- AIC stores a redacted action description, caller, decision and final response.
- Default command allowlist is restricted to `patch`, `rollout`, and `scale`; `delete`, `drain`, RBAC, node and storage actions are excluded.

## Task 1: Approval contract and persistence

**Files:**
- Modify: `deploy/demo/aic-api/src/aic/schemas.py`
- Modify: `deploy/demo/aic-api/src/aic/models.py`
- Create: `deploy/demo/aic-api/migrations/versions/0004_tool_approvals.py`
- Create: `deploy/demo/aic-api/tests/test_tool_approval.py`

- [ ] Write tests for pending approval validation, explicit approver identity, reject behavior and idempotent decisions.
- [ ] Observe RED failure for missing models/service.
- [ ] Add schemas and an approval record linked to the conversation/request.
- [ ] Add migration and run it twice against PostgreSQL.

## Task 2: Holmes streaming approval client

**Files:**
- Modify: `deploy/demo/aic-api/src/aic/holmes.py`
- Test: `deploy/demo/aic-api/tests/test_tool_approval.py`

- [ ] Write parser tests for an `approval_required` SSE event and terminal answer event.
- [ ] Implement bounded SSE parsing with `enable_tool_approval=true`.
- [ ] Implement resume with Holmes `conversation_history` and `tool_decisions`.
- [ ] Preserve response byte and timeout limits.

## Task 3: AIC approval API

**Files:**
- Modify: `deploy/demo/aic-api/src/aic/service.py`
- Modify: `deploy/demo/aic-api/src/aic/main.py`
- Modify: `deploy/demo/aic-api/src/aic/schemas.py`
- Test: `deploy/demo/aic-api/tests/test_tool_approval.py`

- [ ] Make a chat response return `pending_approval` rather than execute a mutation.
- [ ] Add `GET /api/approvals/{approval_id}`.
- [ ] Add `POST /api/approvals/{approval_id}/decision`; require an explicit engineer identity and approve/reject decision.
- [ ] Resume only the paused Holmes conversation and persist final response/audit fields.
- [ ] Reject expired, already decided and malformed approvals.

## Task 4: Remediation MCP and scoped RBAC

**Files:**
- Create: `deploy/demo/holmesgpt/remediation-mcp.yaml`
- Modify: `deploy/demo/holmesgpt/custom_toolset.yaml`
- Modify: `deploy/demo/compose.yaml`
- Modify: `deploy/demo/README.md`

- [ ] Deploy a distinct MCP ServiceAccount and least-privilege ClusterRole.
- [ ] Restrict allowed mutation verbs to `patch`, `rollout`, `scale` and exclude secrets/RBAC/nodes/storage/deletes.
- [ ] Configure the Holmes container with the MCP server and `approval_required_tools: [run_kubectl_command]`.
- [ ] Document activation, API flow, audit query and rollback/cleanup.

## Task 5: Verification

- [ ] Unit test parser/state transitions and observe RED before GREEN.
- [ ] Build/restart changed Compose services and apply only the MCP manifest.
- [ ] Confirm read-only investigation completes without a pending approval.
- [ ] Ask Holmes to patch the disposable NGINX ConfigMap; verify it yields pending approval and does not mutate the cluster.
- [ ] Reject once and prove no mutation occurred.
- [ ] Approve a separate disposable action and verify rollout/pod state through Kubernetes API.
- [ ] Run formatting, typing, compile, focused tests, migration, OpenAPI, health and `git diff --check`.
