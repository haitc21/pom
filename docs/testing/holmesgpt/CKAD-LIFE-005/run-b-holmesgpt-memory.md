# CKAD-LIFE-005 — Run B: HolmesGPT + AIC Memory (Mem0 OSS)

**Namespace:** `holmes-eval-ckad-life-005-run-b`
**Memory:** resolution OOM Run A được seed `infer=False`

## Kết quả

HolmesGPT kiểm chứng `OOMKilled`, exit 137, memory limit 16Mi, events và command `awk`; đề xuất tăng limit hoặc sửa command, kèm xác minh Pod/logs/metrics. Không lệnh nào được thực thi.

Telemetry: 11 tool calls; `prompt_tokens=29587`, `completion_tokens=2916`, `total_tokens=32503`; thời gian khoảng **1m41s**.

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

Paired delta so với Run A: **0 điểm**.
