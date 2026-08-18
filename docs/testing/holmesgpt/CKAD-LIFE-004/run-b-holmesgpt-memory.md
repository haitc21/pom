# CKAD-LIFE-004 — Run B: HolmesGPT + POM Memory (Mem0 OSS)

**Namespace:** `holmes-eval-ckad-life-004-run-b`
**Memory:** resolution Run A được seed `infer=False`; top recall score `0.2574080986747504`

## Kết quả

HolmesGPT kiểm chứng đúng `Unhealthy`/`Killing`, restart count tăng và liveness path `/wrong-live` trả 404. Nó đề xuất sửa path về `/`, xác minh restart count dừng và không thực thi lệnh.

Telemetry: 16 tool calls; `prompt_tokens=54961`, `completion_tokens=2118`, `total_tokens=57079`; thời gian request khoảng **2m23s**.

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
