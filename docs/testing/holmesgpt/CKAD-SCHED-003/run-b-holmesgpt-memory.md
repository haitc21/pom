# CKAD-SCHED-003 — Run B: HolmesGPT + AIC Memory (Mem0 OSS)

**Namespace:** `holmes-eval-ckad-sched-003-run-b`
**Memory:** resolution taint/toleration đã duyệt, seed `infer=False`

HolmesGPT kiểm chứng taint `postops-test=true:NoSchedule`, nodeSelector k8s03 và thiếu toleration; đề xuất toleration hẹp hoặc rollback taint sau approval. Không lệnh nào được thực thi.

Telemetry: 13 tool calls; `prompt_tokens=46179`, `completion_tokens=1340`, `total_tokens=47519`; thời gian khoảng **1m13s**.

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
