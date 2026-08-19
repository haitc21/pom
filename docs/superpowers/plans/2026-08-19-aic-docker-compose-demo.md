# AIC Docker Compose Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng một demo AI Incident Copilot (AIC) bằng Docker Compose, cung cấp một API hội thoại nhiều vòng sử dụng Mem0/Qdrant ở backend và gọi HolmesGPT để điều tra Kubernetes qua model do client chọn khi tạo phiên.

**Architecture:** `aic-api` là điểm vào duy nhất, lưu phiên và bằng chứng trong PostgreSQL, truy xuất memory đã duyệt qua Mem0/Qdrant rồi gọi HolmesGPT qua HTTP. HolmesGPT chạy trong cùng Compose nhưng truy cập cluster Kubernetes PoC bên ngoài bằng kubeconfig chỉ đọc và gọi LiteLLM bên ngoài; PostgreSQL và Qdrant dùng named volume để dữ liệu sống qua restart.

**Tech Stack:** Docker Compose v2; Python 3.12; FastAPI; Pydantic v2; SQLAlchemy 2; Alembic; psycopg 3; httpx; Mem0 OSS 2.0.18; FastEmbed 0.8.0; Qdrant; PostgreSQL 16; HolmesGPT 0.39.0; pytest.

**Spec:** `outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md`

## Global Constraints

- Task ID: `AIC-DEMO-001`.
- API demo chỉ triển khai Run B: Mem0 luôn hoạt động ở backend, client không được bật/tắt memory.
- Client bắt buộc chọn model khi tạo phiên; model được cố định suốt phiên và hiện chỉ allowlist `mistral-3.5`.
- Demo không tích hợp Redmine, không xây UI, không tự thi hành lệnh khắc phục và không quản lý Skill approval.
- HolmesGPT, PostgreSQL và Qdrant chạy bằng Docker Compose; Kubernetes, Prometheus, Loki và LiteLLM là hệ thống ngoài Compose.
- Cluster Kubernetes PoC, `k8s-storage`, NFS, PostgreSQL phục vụ Grafana và `k8s-lb` phải tiếp tục chạy trong suốt demo; chúng là dependency ngoài Compose, không phải dịch vụ AIC trùng lặp cần tắt.
- HolmesGPT chỉ có quyền đọc Kubernetes; không mount Docker socket và không cấp quyền ghi cluster.
- Chỉ resolution được kỹ sư xác nhận mới được lập chỉ mục memory; câu trả lời AI và hội thoại thô không tự trở thành tri thức chuẩn.
- Không commit `.env`, API key, password, kubeconfig, certificate hay output chứa secret; repo chỉ chứa `.env.example` và kubeconfig template không có credential.
- Dữ liệu PostgreSQL/Qdrant dùng named volume; vận hành bình thường dùng `docker compose stop`, không dùng `docker compose down -v`.
- Python runtime phải là 3.12; không cài hoặc kéo Python 3.13 vào host.
- Mọi thay đổi hành vi tuân thủ RED-GREEN-REFACTOR và phải được review độc lập trước khi hoàn tất.

---

## Testable Outcome

Demo đạt khi một máy host mới có Docker Compose, `.env` hợp lệ và kubeconfig read-only có thể:

1. Chạy `docker compose up -d --build` để khởi động bốn service khỏe mạnh: `postgres`, `qdrant`, `holmesgpt`, `aic-api`.
2. Tạo phiên qua `POST /api/chat` với `conversation_id=null`, `model=mistral-3.5` và nhận `conversation_id`, câu trả lời HolmesGPT, iteration cùng danh sách memory reference.
3. Gửi lượt tiếp theo cùng `conversation_id`, nhận command/output do kỹ sư thực hiện, và giữ đầy đủ ngữ cảnh nhiều vòng trong PostgreSQL.
4. Từ chối model khác model của phiên bằng HTTP 409 và từ chối model ngoài allowlist bằng HTTP 422.
5. Restart toàn bộ Compose mà vẫn đọc được hội thoại từ PostgreSQL và memory từ Qdrant.
6. Seed một resolution đã duyệt, truy xuất nó cho mô tả tương đồng, nhưng không truy xuất một hội thoại chưa duyệt như tri thức chuẩn.
7. HolmesGPT đọc được cluster PoC và không thể tạo, sửa hoặc xóa Kubernetes resource.

## Acceptance Criteria

- `POST /api/chat` là API nghiệp vụ duy nhất cần cho demo; `/health` chỉ phục vụ healthcheck.
- Lượt đầu tạo conversation atomically trước khi gọi HolmesGPT; lỗi downstream được lưu với trạng thái `failed` và có thể retry bằng request có `request_id` cũ mà không nhân đôi message.
- Lượt sau nối đúng conversation, tăng iteration đúng một lần và lưu message, command output, Holmes response, memory references.
- Response và log không lộ `LITELLM_API_KEY`, password, bearer token hoặc nội dung kubeconfig.
- AIC không chạy command do HolmesGPT đề xuất; command/output trong API chỉ là bằng chứng do người dùng gửi lên.
- Compose pin version image/package, có healthcheck và startup dependency rõ ràng.
- Focused tests, full tests, Compose config validation, secret scan và live smoke test đều có bằng chứng mới.

## Out of Scope

- Đồng bộ/ghi ngược Redmine, Grafana UI, multi-tenant authentication, SSO/RBAC người dùng và production HA.
- Tự động chạy shell/kubectl remediation, tự động đóng ticket hoặc tự động approve resolution.
- Qdrant cluster, PostgreSQL replication/backup, TLS nội bộ Compose và Kubernetes chạy bên trong Compose.
- Run A không memory, so sánh model, model fallback do client điều khiển và thay model giữa conversation.
- Tạo/phê duyệt `SKILL.md`; demo chỉ seed và recall resolution đã duyệt.

## Contract and Version Decisions

- API version dùng prefix `/api`, chưa phát hành compatibility guarantee; thay đổi breaking trước PoC hoàn tất không cần `/v2` nhưng phải cập nhật OpenAPI và contract tests cùng commit.
- Request tạo phiên:

```json
{
  "request_id": "018f6d75-9d31-7f2a-b81c-aea4922eb321",
  "conversation_id": null,
  "model": "mistral-3.5",
  "message": "Pod checkout-api đang CrashLoopBackOff trong namespace demo.",
  "context": {"cluster": "k8s-poc", "namespace": "demo"},
  "command_outputs": []
}
```

- Request lượt sau dùng cùng schema, đặt `conversation_id` bằng UUID đã nhận và có thể gửi:

```json
{
  "command": "kubectl -n demo describe pod checkout-api-abc",
  "exit_code": 0,
  "output": "Last State: Terminated; Reason: OOMKilled; Exit Code: 137"
}
```

- Response thành công:

```json
{
  "conversation_id": "018f6d8b-5488-7dd0-b107-04228cf379f2",
  "request_id": "018f6d75-9d31-7f2a-b81c-aea4922eb321",
  "model": "mistral-3.5",
  "iteration": 1,
  "status": "completed",
  "answer": "...",
  "memory_references": [
    {"memory_id": "mem-123", "score": 0.82, "resolution_id": "res-123"}
  ]
}
```

- `request_id` là UUIDv7 do client tạo và là idempotency key; unique theo toàn hệ thống. API từ chối UUID version khác bằng HTTP 422.
- Pin ban đầu: `python:3.12-slim`, `postgres:16`, `robustadev/holmes:0.39.0`, `mem0ai==2.0.18`, `fastembed==0.8.0`, `qdrant-client==1.19.0`, `httpx==0.28.1`. Worker phải pin dependency Python trong `uv.lock` và pin digest/tag Qdrant tương thích trực tiếp trong `compose.yaml`; không dùng `latest`.

## File Map and Blast Radius

`.codegraph/` không tồn tại tại thời điểm lập kế hoạch, vì vậy blast radius được xác định từ file tree và import trực tiếp. Code mới nằm độc lập dưới `deploy/demo/`; điểm giao với PoC hiện tại chỉ là hợp đồng Holmes `/api/chat`, model `mistral-3.5`, kubeconfig và endpoint cluster/telemetry.

```text
deploy/demo/
├── .env.example                         # danh mục biến môi trường không chứa secret
├── .gitignore                           # loại .env, kubeconfig thật và artifact runtime
├── compose.yaml                         # topology, volume, network, healthcheck
├── README.md                            # quick start và giới hạn demo
├── aic-api/
│   ├── Dockerfile                       # Python 3.12 non-root image
│   ├── pyproject.toml                   # dependency/runtime/tool config
│   ├── uv.lock                          # dependency lock tái lập
│   ├── alembic.ini
│   ├── migrations/env.py
│   ├── migrations/versions/0001_initial.py
│   ├── src/aic/__init__.py
│   ├── src/aic/config.py                # validate env và model allowlist
│   ├── src/aic/db.py                    # engine/session lifecycle
│   ├── src/aic/models.py                # PostgreSQL ORM
│   ├── src/aic/schemas.py               # request/response contract
│   ├── src/aic/redaction.py             # credential redaction
│   ├── src/aic/memory.py                # Mem0/Qdrant adapter
│   ├── src/aic/holmes.py                # HolmesGPT HTTP adapter
│   ├── src/aic/service.py               # orchestration/idempotency
│   ├── src/aic/main.py                  # FastAPI routes/lifespan
│   └── tests/                           # unit, contract, integration tests
├── holmesgpt/
│   ├── model_list.yaml                  # mistral-3.5 → LiteLLM mapping
│   └── kubeconfig.example.yaml          # shape only, no cert/token
├── scripts/
│   ├── export-readonly-kubeconfig.sh    # produce ignored self-contained kubeconfig
│   ├── seed-approved-resolution.py      # seed only approved fixture
│   └── smoke-test.sh                    # deterministic live flow
└── postgres/init/                       # intentionally empty; Alembic owns schema

docs/runbooks/aic-docker-compose-demo.md # redacted build/run/verify/stop/recovery evidence
```

Existing files intentionally unchanged by implementation: `deploy/k8s/**`, `scripts/holmes_eval/**`, test result documents and the main idea document. If implementation discovers a required contract difference, stop and return to planning before changing these paths.

## Current PoC Service Transition

- Giữ chạy năm VM `k8s01`, `k8s02`, `k8s03`, `k8s-storage`, `k8s-lb` để cung cấp Kubernetes, Prometheus, Loki, Grafana, NFS và đường truy cập từ host.
- Giữ PostgreSQL trên `k8s-storage`: database hiện tại là `grafana`, không phải database nghiệp vụ AIC trong Compose.
- Scale `deployment/holmesgpt-holmes` trong namespace `holmesgpt` về 0 trước khi bật HolmesGPT Compose; không uninstall Helm release và không xóa Service, Secret hay cấu hình.
- Mem0 và embedded Qdrant cũ không có daemon thường trực; giữ nguyên `/data/k8s-poc/mem0` để bảo toàn dữ liệu thử nghiệm nhưng không mount nó vào demo mới.
- Không tắt VM khi dừng demo. Mặc định chỉ chạy `docker compose stop`; việc shutdown hạ tầng KVM là một thao tác vận hành riêng cần yêu cầu rõ ràng.

## Threat and Security Scope

- Trust boundaries: untrusted API input; untrusted command output/log text; Mem0 recalled text; Holmes/model output; external LiteLLM; read-only Kubernetes credential.
- Prompt injection in ticket, logs or recalled memory must remain quoted data; system prompt states memory is non-authoritative and current evidence must verify it.
- Enforce maximums: message 32 KiB, context JSON 32 KiB, each command output 256 KiB, at most 20 command outputs/request, Holmes response 1 MiB, maximum 20 iterations/conversation.
- Redact case-insensitive bearer token, API key, password, private-key block and kubeconfig credential patterns before database persistence and structured logging.
- API must not expose arbitrary target URL, command execution, file path or model provider fields.
- Container runs non-root with dropped capabilities and read-only root filesystem where compatible; writable tmpfs only for `/tmp`; no privileged mode or Docker socket.
- Kubeconfig is mounted `:ro`, generated for the existing read-only service account, and ignored by Git.
- Secret scan must cover tracked diff and Compose-rendered output; rendered environment values must never be attached to the runbook.

---

### Task 1: Lock the API contract and test harness

**Files:**
- Create: `deploy/demo/aic-api/pyproject.toml`
- Create: `deploy/demo/aic-api/uv.lock`
- Create: `deploy/demo/aic-api/src/aic/__init__.py`
- Create: `deploy/demo/aic-api/src/aic/config.py`
- Create: `deploy/demo/aic-api/src/aic/schemas.py`
- Create: `deploy/demo/aic-api/tests/test_contract.py`

**Interfaces:**
- Produces: `Settings`, `ChatRequest`, `CommandOutput`, `ChatResponse`, `MemoryReference`.
- `ChatRequest.model: Literal["mistral-3.5"]`; `conversation_id: UUID | None`; `request_id: UUIDv7`; bounded strings/lists per security scope.

- [ ] **Step 1: Write RED contract tests** covering valid first/follow-up request, rejection of UUIDv4/non-v7 `request_id`, unknown model, oversized message/output, more than 20 outputs and response serialization with memory provenance.
- [ ] **Step 2: Run** `cd deploy/demo/aic-api && uv run pytest tests/test_contract.py -q`; expect collection failure because `aic.schemas` does not exist.
- [ ] **Step 3: Record the observed failure** in `docs/runbooks/aic-docker-compose-demo.md` with command, timestamp and concise non-secret error.
- [ ] **Step 4: Implement minimal Pydantic models and environment settings** with exact limits and `AIC_ALLOWED_MODELS=mistral-3.5`.
- [ ] **Step 5: Run the focused test** and expect all contract cases PASS.
- [ ] **Step 6: Refactor** shared constrained types without changing OpenAPI shape; rerun focused tests.
- [ ] **Step 7: Proposed commit boundary:** `feat(aic): define demo chat contract` (do not execute Git mutation without current-turn authorization).

### Task 2: Persist conversations, evidence and idempotency

**Files:**
- Create: `deploy/demo/aic-api/alembic.ini`
- Create: `deploy/demo/aic-api/migrations/env.py`
- Create: `deploy/demo/aic-api/migrations/versions/0001_initial.py`
- Create: `deploy/demo/aic-api/src/aic/db.py`
- Create: `deploy/demo/aic-api/src/aic/models.py`
- Create: `deploy/demo/aic-api/tests/test_persistence.py`

**Interfaces:**
- Produces: tables `conversations`, `requests`, `messages`, `command_outputs`, `memory_references`.
- Conversation fields: UUID id, model, status, context JSONB, iteration, timestamps.
- Request fields: UUID request_id unique, conversation_id, status, error_code, timestamps.

- [ ] **Step 1: Write RED PostgreSQL tests** for atomic conversation creation, ordered messages, idempotent duplicate `request_id`, model immutability and failed-request persistence.
- [ ] **Step 2: Start disposable test DB** with `docker compose -f compose.test.yaml up -d postgres-test`, run the focused test and expect missing migration/model failure.
- [ ] **Step 3: Implement initial Alembic migration and SQLAlchemy models** including foreign keys, unique request ID and index on `(conversation_id, created_at)`.
- [ ] **Step 4: Run `alembic upgrade head` twice**; expect both runs to succeed and schema head unchanged.
- [ ] **Step 5: Run focused tests** and expect PASS, then run downgrade/upgrade against only the disposable DB.
- [ ] **Step 6: Refactor transaction helpers** into `db.py`; rerun persistence tests.
- [ ] **Step 7: Stop disposable DB without deleting named development volumes**; test-only anonymous resources may be removed after their IDs are recorded.
- [ ] **Step 8: Proposed commit boundary:** `feat(aic): persist incident conversations`.

### Task 3: Add redaction and safe prompt construction

**Files:**
- Create: `deploy/demo/aic-api/src/aic/redaction.py`
- Create: `deploy/demo/aic-api/tests/test_redaction.py`
- Create: `deploy/demo/aic-api/tests/test_prompt.py`
- Modify: `deploy/demo/aic-api/src/aic/service.py`

**Interfaces:**
- Produces: `redact(text: str) -> str` and `build_holmes_prompt(message, context, outputs, memories) -> str`.
- Memory blocks carry `resolution_id`, score and quoted content marked non-authoritative.

- [ ] **Step 1: Write RED tests** for bearer token, API key, password, PEM private key and kubeconfig token redaction; include a benign Kubernetes log that must remain unchanged.
- [ ] **Step 2: Write RED prompt-injection tests** proving a recalled instruction cannot replace the fixed system policy and every memory retains its provenance.
- [ ] **Step 3: Run focused tests** and expect missing functions.
- [ ] **Step 4: Implement deterministic redaction before persistence/logging and prompt construction with explicit data delimiters.**
- [ ] **Step 5: Run focused tests** and expect PASS; inspect failure messages to ensure test secrets are synthetic.
- [ ] **Step 6: Refactor patterns into compiled expressions and rerun tests.**
- [ ] **Step 7: Proposed commit boundary:** `feat(aic): redact evidence and isolate memory context`.

### Task 4: Integrate Mem0 with remote Qdrant

**Files:**
- Create: `deploy/demo/aic-api/src/aic/memory.py`
- Create: `deploy/demo/aic-api/tests/test_memory.py`
- Create: `deploy/demo/scripts/seed-approved-resolution.py`

**Interfaces:**
- Produces: `MemoryStore.search(query, context, limit=5) -> list[RecalledMemory]` and `MemoryStore.add_approved(resolution) -> str`.
- Consumes: `QDRANT_URL`, `MEM0_COLLECTION`, LiteLLM settings and FastEmbed model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with 384 dimensions.

- [ ] **Step 1: Write RED adapter tests** with a fake Mem0 client: filter `approval_status=approved`, retain score/source metadata, return empty list safely and reject unapproved writes.
- [ ] **Step 2: Run focused tests** and expect `MemoryStore` import failure.
- [ ] **Step 3: Implement the adapter** so AIC owns approval checks and Mem0 only extracts/searches; never treat Mem0 as the business database.
- [ ] **Step 4: Run focused tests** and expect PASS.
- [ ] **Step 5: Start Qdrant test service and run integration test** that seeds an approved CrashLoopBackOff resolution, recalls a paraphrase, and proves an unapproved fixture is absent.
- [ ] **Step 6: Restart Qdrant and repeat recall** to verify persistent collection data.
- [ ] **Step 7: Refactor client initialization into FastAPI lifespan; rerun unit and integration tests.**
- [ ] **Step 8: Proposed commit boundary:** `feat(aic): retrieve approved incident memory`.

### Task 5: Integrate HolmesGPT and orchestrate iterative chat

**Files:**
- Create: `deploy/demo/aic-api/src/aic/holmes.py`
- Create: `deploy/demo/aic-api/src/aic/service.py`
- Create: `deploy/demo/aic-api/src/aic/main.py`
- Create: `deploy/demo/aic-api/tests/test_holmes.py`
- Create: `deploy/demo/aic-api/tests/test_chat_api.py`

**Interfaces:**
- Produces: `HolmesClient.chat(prompt: str, model: str) -> str`, `ChatService.handle(ChatRequest) -> ChatResponse`, `POST /api/chat`, `GET /health`.
- Consumes: Holmes contract `POST {HOLMES_URL}/api/chat` body `{"ask": prompt, "model": "mistral-3.5"}`.

- [ ] **Step 1: Write RED Holmes adapter tests** for success, timeout, non-2xx, malformed body and maximum response size.
- [ ] **Step 2: Write RED API tests** for first message, follow-up, duplicate request replay, conversation/model mismatch (409), iteration limit (409), unknown conversation (404) and downstream failure (502 with persisted failed status).
- [ ] **Step 3: Run focused tests** and expect missing client/service/routes.
- [ ] **Step 4: Implement minimal async Holmes client and orchestration transaction boundaries:** persist sanitized input, recall approved memories, call Holmes, persist answer/references, then complete request.
- [ ] **Step 5: Implement idempotent replay:** a completed duplicate returns stored response; an in-progress duplicate returns 409; a failed duplicate retries without adding a second user message.
- [ ] **Step 6: Run focused adapter/API tests** and expect PASS.
- [ ] **Step 7: Refactor error mapping into typed domain errors and rerun all `aic-api` tests.**
- [ ] **Step 8: Proposed commit boundary:** `feat(aic): add iterative incident chat API`.

### Task 6: Package HolmesGPT with read-only cluster access

**Files:**
- Create: `deploy/demo/holmesgpt/model_list.yaml`
- Create: `deploy/demo/holmesgpt/kubeconfig.example.yaml`
- Create: `deploy/demo/scripts/export-readonly-kubeconfig.sh`
- Create: `deploy/demo/tests/test_holmes_config.py`

**Interfaces:**
- Model key `mistral-3.5` maps to `openai/mistral-3.5` at `${LITELLM_BASE_URL}`.
- Generated ignored file: `deploy/demo/holmesgpt/kubeconfig` with embedded CA/client data or service-account token and API server reachable from container.

- [ ] **Step 1: Write RED config tests** asserting model label/mapping, disabled internet/bash/write tools, no inline API key and kubeconfig mounted read-only.
- [ ] **Step 2: Run focused test** and expect missing config files.
- [ ] **Step 3: Add Holmes config** equivalent to current PoC read-only toolsets for Kubernetes, Prometheus and Loki, with secrets supplied only through environment.
- [ ] **Step 4: Implement kubeconfig export script** that validates context `k8s-poc`, writes mode 0600, embeds referenced certificate data and refuses a writable service account role.
- [ ] **Step 5: Run config tests** and expect PASS.
- [ ] **Step 6: Live negative RBAC test:** from Holmes container run `kubectl auth can-i get pods -A` (yes) and `kubectl auth can-i create deployments -A` (no); record both.
- [ ] **Step 7: Proposed commit boundary:** `build(aic): package read-only HolmesGPT`.

### Task 7: Assemble and harden Docker Compose

**Files:**
- Create: `deploy/demo/compose.yaml`
- Create: `deploy/demo/compose.test.yaml`
- Create: `deploy/demo/.env.example`
- Create: `deploy/demo/.gitignore`
- Create: `deploy/demo/aic-api/Dockerfile`
- Create: `deploy/demo/README.md`
- Create: `deploy/demo/tests/test_compose.py`

**Interfaces:**
- Services: `postgres:5432`, `qdrant:6333`, `holmesgpt:5050` internal, `aic-api:${AIC_PORT:-8080}` published.
- Named volumes: `aic_postgres_data`, `aic_qdrant_data`, optional `aic_holmes_cache`.
- Required env: `LITELLM_API_KEY`, `LITELLM_BASE_URL`, `AIC_MODEL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `QDRANT_URL`, `MEM0_COLLECTION`, `HOLMES_URL`, `KUBECONFIG_PATH`, `K8S_CLUSTER_NAME`.

- [ ] **Step 1: Write RED Compose tests** for exact services, pinned images, healthchecks, dependency conditions, named volumes, non-root/read-only security settings, no Docker socket, no host network and read-only kubeconfig mount.
- [ ] **Step 2: Run** `docker compose --env-file deploy/demo/.env.example -f deploy/demo/compose.yaml config`; expect missing-file/config failure before Compose exists.
- [ ] **Step 3: Build Python 3.12 non-root image** using locked dependencies, deterministic entrypoint that runs `alembic upgrade head` then starts Uvicorn, and a container healthcheck.
- [ ] **Step 4: Define Compose services** on one bridge network with outbound access to `10.77.0.0/24` and LiteLLM; use service DNS internally and expose only AIC API by default.
- [ ] **Step 5: Add `.env.example` placeholders and `.gitignore` rules** for `.env`, real kubeconfig, DB dumps, Qdrant files and smoke-test output.
- [ ] **Step 6: Validate resolved Compose config** with synthetic non-secret values; expect PASS and inspect that no value named `API_KEY` has a real credential.
- [ ] **Step 7: Run container/security tests** and image vulnerability scan; Critical/High findings in application/runtime dependencies block completion until fixed or explicitly accepted.
- [ ] **Step 8: Proposed commit boundary:** `build(aic): add reproducible Docker Compose demo`.

### Task 8: End-to-end verification, restart and cleanup paths

**Files:**
- Create: `deploy/demo/scripts/smoke-test.sh`
- Create: `deploy/demo/tests/test_live_demo.py`
- Create: `docs/runbooks/aic-docker-compose-demo.md`
- Modify: `deploy/demo/README.md`

**Interfaces:**
- Smoke script consumes `AIC_BASE_URL` and fixture namespace/workload; outputs only redacted JSON summary.
- Runbook records timestamps, image digests, commands, pass/fail counts, container IDs, review closure and cleanup ledger.

- [ ] **Step 1: Snapshot the five KVM PoC VMs** with a new task-scoped snapshot name before creating a fault fixture; record names only, not credentials.
- [ ] **Step 2: Start infrastructure in dependency order:** `k8s-storage`, `k8s01`, `k8s02`, `k8s03`, then `k8s-lb`; verify nodes Ready, NFS, Holmes target access, Prometheus and Loki before Compose smoke testing.
- [ ] **Step 3: Write RED live test** for create conversation → provide command output → receive second answer → replay same request → verify same response/iteration.
- [ ] **Step 4: Run the live test before final wiring** and record the expected failing endpoint/dependency reason.
- [ ] **Step 5: Run `docker compose up -d --build` and poll every healthcheck to terminal healthy; timeout is a failure, not a reason to skip.**
- [ ] **Step 6: Seed one approved resolution and execute smoke test** against a disposable CrashLoopBackOff or OOMKilled fixture; verify memory reference includes resolution provenance.
- [ ] **Step 7: Exercise negative paths:** bad model 422, model change 409, unknown conversation 404, duplicate request replay, unapproved memory absent and Kubernetes create permission denied.
- [ ] **Step 8: Exercise restart path:** `docker compose restart`, wait healthy, retrieve the same conversation and memory, then continue one iteration without duplication.
- [ ] **Step 9: Run focused and full gates:** `uv run pytest -q`, `ruff check .`, `ruff format --check .`, `mypy src`, migration upgrade check, Compose config test, `git diff --check`, tracked-file secret scan and image scan.
- [ ] **Step 10: Request independent review** with two passes: spec/contract acceptance, then quality/failure/security/tests; validate and remediate every finding, rerun affected gates, and obtain final re-review.
- [ ] **Step 11: Cleanup only task-created fault fixtures** and prove their absence with `kubectl`; retain Compose named volumes and stop services using `docker compose stop`.
- [ ] **Step 12: Keep external PoC infrastructure running** and verify all Kubernetes nodes, Prometheus, Loki, NFS, PostgreSQL for Grafana and `k8s-lb` remain healthy after `docker compose stop`.
- [ ] **Step 13: Complete the redacted runbook** with limitations: local-only demo, external cluster/LiteLLM dependency, no auth/HA/Redmine and no automated remediation.
- [ ] **Step 14: Proposed commit boundary:** `test(aic): verify persistent memory demo end to end`.

## Focused and Full Verification Commands

```bash
cd deploy/demo/aic-api
uv sync --frozen
uv run pytest tests/test_contract.py tests/test_persistence.py tests/test_redaction.py -q
uv run pytest tests/test_memory.py tests/test_holmes.py tests/test_chat_api.py -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src

cd /home/haitc/project/pom
docker compose --env-file deploy/demo/.env -f deploy/demo/compose.yaml config --quiet
docker compose --env-file deploy/demo/.env -f deploy/demo/compose.yaml up -d --build
python3 -m pytest deploy/demo/tests -q
bash deploy/demo/scripts/smoke-test.sh
git diff --check
git status --short
```

The worker must invoke the repository-approved secret scanner and container vulnerability scanner available on the host; if none is installed, stop and report the missing gate instead of silently claiming it passed.

## Operational Start/Stop Contract

Start cluster dependencies before Compose:

```text
k8s-storage → k8s01 → k8s02 + k8s03 → k8s-lb → Docker Compose
```

Stop only the Compose demo while retaining its named volumes and all external PoC dependencies:

```text
docker compose stop → Kubernetes/monitoring/storage/LB remain running
```

`docker compose stop` preserves named volumes. `docker compose down` may remove containers/network but not named volumes unless `-v` is supplied; the demo runbook must prohibit `down -v` during normal operation.

## Proposed Commit Series

1. `feat(aic): define demo chat contract`
2. `feat(aic): persist incident conversations`
3. `feat(aic): redact evidence and isolate memory context`
4. `feat(aic): retrieve approved incident memory`
5. `feat(aic): add iterative incident chat API`
6. `build(aic): package read-only HolmesGPT`
7. `build(aic): add reproducible Docker Compose demo`
8. `test(aic): verify persistent memory demo end to end`

These are proposals only. Implementation must not stage, commit or push without explicit authorization in the turn where that Git action is requested.
