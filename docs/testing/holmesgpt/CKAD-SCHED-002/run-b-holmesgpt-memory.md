# CKAD-SCHED-002 — Run B: HolmesGPT + POM Memory (Mem0 OSS)

**Namespace:** `holmes-eval-ckad-sched-002-run-b`
**Memory:** resolution affinity đã duyệt được seed `infer=False`

HolmesGPT kiểm chứng nodeAffinity, node labels và event scheduler hiện tại; xác định đúng hostname không tồn tại, tách taint control-plane thành nguyên nhân phụ, và đề xuất sửa constraint. Không lệnh nào được thực thi.

Telemetry: 9 tool calls; `prompt_tokens=21772`, `completion_tokens=1718`, `total_tokens=23490`; thời gian khoảng **0m59s**.

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
