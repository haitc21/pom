# CKAD-LIFE-003 — Run A: HolmesGPT only

**Ngày chạy:** 2026-08-18
**Mode:** HolmesGPT only; không truy hồi POM Memory
**Namespace:** `holmes-eval-ckad-life-003-run-a`

## Fault và oracle

Deployment NGINX dùng image đã cache `docker.io/library/nginx:1.27`, có readiness probe HTTP `GET /wrong-ready` trên port 80. NGINX mặc định trả 404 cho path này.

- Pod được schedule trên `k8s03`, phase `Running`, container không restart.
- `Ready=False`, `ContainersNotReady`.
- Deployment `0/1` available.
- Service selector khớp Pod nhưng Endpoints rỗng.
- Event: `Readiness probe failed: HTTP probe failed with statuscode: 404`.

## Kết quả

HolmesGPT xác định chính xác readiness probe sai path, phân biệt được Pod Running với Pod Ready, liên kết được Endpoint rỗng với readiness, và đề xuất đổi path thành `/` hoặc `/index.html`. Cách xác minh gồm Pod Ready, Service endpoint và HTTP 200.

Telemetry: 12 tool calls; `prompt_tokens=52032`, `completion_tokens=2062`, `total_tokens=54094`; thời gian xử lý từ log request đến HTTP 200 khoảng **1m35s**.

## Chấm điểm

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

## Cleanup

Namespace đã xóa và xác nhận không còn; không sửa workload hay hạ tầng PoC.
