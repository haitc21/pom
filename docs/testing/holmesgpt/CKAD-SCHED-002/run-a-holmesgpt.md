# CKAD-SCHED-002 — Run A: HolmesGPT only

**Namespace:** `holmes-eval-ckad-sched-002-run-a`
**Fault:** required nodeAffinity tới hostname không tồn tại

HolmesGPT xác định đúng `Pending`, `FailedScheduling`, node affinity mismatch và control-plane taint phụ. Nó đề xuất sửa/xóa affinity và xác minh Pod `Running`; không thực thi lệnh.

Telemetry: 11 tool calls; `prompt_tokens=22586`, `completion_tokens=2100`, `total_tokens=24686`; thời gian khoảng **1m13s**.

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
