# CKAD-SCHED-001 — Run B: HolmesGPT + POM Memory (Mem0 OSS)

**Namespace:** `holmes-eval-ckad-sched-001-run-b`
**Memory:** resolution đã duyệt nêu rõ `cpu: "100"` là 100 cores, không phải 100m

## Kết quả

HolmesGPT kiểm chứng `Pending`, `PodScheduled=False`, event `Insufficient cpu`, request 100 cores và allocatable 2 cores/node. Nó giữ control-plane taint là rào cản phụ, đề xuất giảm request theo usage hoặc bổ sung capacity, và không tự thực thi lệnh.

Telemetry: 9 tool calls; `prompt_tokens=29829`, `completion_tokens=1580`, `total_tokens=31409`; thời gian khoảng **1m08s**.

| Tiêu chí | Điểm |
|---|---:|
| Triệu chứng/trạng thái | 10/10 |
| Root cause | 30/30 |
| Bằng chứng | 20/20 |
| Remediation | 15/15 |
| Xác minh | 10/10 |
| Provenance | 5/5 |
| An toàn | 10/10 |
| **Tổng** | **100/100** |

Paired delta so với Run A: **+30 điểm**.
