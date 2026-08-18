# CKAD-LIFE-001 — Run B: HolmesGPT + POM Memory (Mem0 OSS)

**Ngày chạy:** 2026-08-18
**Trạng thái:** Đã hoàn tất
**Mode:** HolmesGPT + POM Memory (Mem0 OSS)
**Runtime:** Python 3.12 venv trên host; Mem0 2.0.18, FastEmbed 0.8.0, Qdrant embedded
**Snapshot:** dùng campaign snapshot `poc-eval-20260818`
**Namespace:** `holmes-eval-ckad-life-001-run-b` (đã cleanup)

## Chuẩn bị local memory

Mem0 chạy trên host ở `/data/k8s-poc/mem0/venv`, dữ liệu Qdrant/history ở `/data/k8s-poc/mem0/data`. Runtime không nằm trong Git. LiteLLM chỉ được dùng cho HolmesGPT; embedding do FastEmbed chạy local vì LiteLLM hiện không có `/v1/embeddings`.

Resolution đã duyệt từ Run A được seed bằng `infer=False` với metadata:

- `case_id=CKAD-LIFE-001`;
- `resolution_id=run-a-approved-resolution`;
- `approval_status=approved`;
- `source=docs/testing/holmesgpt/CKAD-LIFE-001/run-a-holmesgpt.md`.

## Oracle độc lập

- Deployment `ckad-life-001` trong namespace Run B có `unavailableReplicas=1` và condition `Available=False` với `MinimumReplicasUnavailable`.
- Pod được schedule trên `k8s03`, image `docker.io/library/nginx:1.27` đã có sẵn.
- Container không ready, restart count tăng, exit code `1`.
- Log: `fatal: configuration file /etc/demo/app.yaml not found`.
- Event: `BackOff` sau khi container start và thoát.

## Mem0 recall

- `seed_count`: 1
- `retrieved_count`: 1
- `memory_id`: `e10c2972-21ec-40ca-a2fb-1ebf92a3e590`
- `score`: `0.27154895927784634`
- Nội dung recall khớp resolution Run A: command/args ghi lỗi thiếu file rồi `exit 1`, cần khôi phục entrypoint NGINX.

Memory được chèn vào prompt dưới nhãn tham khảo không có tính quyết định; HolmesGPT vẫn phải kiểm chứng dữ liệu namespace Run B.

## Kết quả HolmesGPT

HolmesGPT đã xác minh độc lập:

- Deployment không đạt minimum availability.
- Pod phase `Running` nhưng container không ready và liên tục restart.
- Container `nginx` terminated với exit code `1`.
- `command`/`args` ghi lỗi `/etc/demo/app.yaml not found` rồi thoát `1`, ghi đè entrypoint của NGINX.
- Event `BackOff`, image đã được pull/present và Pod đã schedule thành công.
- Không có bằng chứng cho image pull failure, scheduling failure, OOM, resource pressure hoặc network failure.
- Đề xuất an toàn: xóa command/args bị inject hoặc khôi phục entrypoint NGINX; không tự thực hiện.

HolmesGPT trả về 16 tool calls, `prompt_tokens=32814`, `completion_tokens=2252`, `total_tokens=35066`, `finish_reason=stop`. Chưa so sánh latency/token với Run A vì Run A chưa lưu cùng telemetry.

## Đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Nhận diện triệu chứng/trạng thái | 10/10 |
| Root cause | 30/30 |
| Bằng chứng | 20/20 |
| Remediation | 15/15 |
| Xác minh phục hồi | 10/10 |
| Phạm vi/provenance | 5/5 |
| An toàn | 10/10 |
| **Tổng** | **100/100** |

### So sánh với Run A

- Run A HolmesGPT only: `88/100`.
- Run B HolmesGPT + Mem0: `100/100`.
- Chênh lệch: `+12` điểm.
- Memory recall đúng case và không gây anchoring sai; HolmesGPT vẫn kiểm tra namespace, image, command/args, log và event hiện tại.
- Đây là exact recurrence với resource/namespace mới, chưa phải đánh giá analogous hoặc hard-negative.

## Cleanup và hạ tầng

- Namespace `holmes-eval-ckad-life-001-run-b` đã xóa và xác nhận không còn.
- Ba node Kubernetes vẫn `Ready` trên v1.35.7.
- HolmesGPT vẫn `1/1 Running`.
- Port-forward tạm thời đã dừng.
- File raw response nằm ngoài repo tại `/data/k8s-poc/mem0/run-b-result.json`; không chứa API key và không được commit.

Không điền kết quả này như bằng chứng cho hard-negative, paraphrase hoặc cross-project; các cohort đó cần chạy riêng.

Run B đã hoàn tất; các cohort paraphrase, analogous, cross-project và hard-negative chưa được thực hiện trong bài này.
