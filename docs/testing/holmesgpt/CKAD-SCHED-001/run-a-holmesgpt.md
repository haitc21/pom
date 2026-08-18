# CKAD-SCHED-001 — Run A: HolmesGPT only

**Namespace:** `holmes-eval-ckad-sched-001-run-a`
**Fault:** container request/limit `cpu: "100"`, không có node nào đủ CPU

## Kết quả

HolmesGPT xác định đúng `Pending`, `FailedScheduling`, `Insufficient cpu` và control-plane taint nhưng đọc sai `cpu: "100"` thành 100m/0.1 core. Vì vậy nó đề xuất giảm xuống 50m, không xử lý đúng root cause semantic của manifest.

Telemetry: 16 tool calls; `prompt_tokens=44629`, `completion_tokens=1673`, `total_tokens=46302`; thời gian khoảng **1m22s**.

| Tiêu chí | Điểm |
|---|---:|
| Triệu chứng/trạng thái | 10/10 |
| Root cause | 10/30 |
| Bằng chứng | 18/20 |
| Remediation | 8/15 |
| Xác minh | 10/10 |
| Provenance | 5/5 |
| An toàn | 9/10 |
| **Tổng** | **70/100** |
