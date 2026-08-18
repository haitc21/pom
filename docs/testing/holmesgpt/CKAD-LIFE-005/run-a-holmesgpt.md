# CKAD-LIFE-005 — Run A: HolmesGPT only

**Namespace:** `holmes-eval-ckad-life-005-run-a`
**Fault:** NGINX image cached, command `awk` tạo chuỗi lớn, memory limit `16Mi`

## Kết quả

HolmesGPT xác định đúng `OOMKilled`, exit code 137, limit 16Mi và command allocation là nguyên nhân. Nó loại trừ image pull, scheduling và node OOM; đề xuất tăng limit hoặc bỏ command và không thực thi lệnh.

Telemetry: 14 tool calls; `prompt_tokens=27429`, `completion_tokens=1547`, `total_tokens=28976`; thời gian khoảng **1m20s**.

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
