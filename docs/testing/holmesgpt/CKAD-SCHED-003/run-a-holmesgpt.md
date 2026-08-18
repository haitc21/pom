# CKAD-SCHED-003 — Run A: HolmesGPT only

**Namespace:** `holmes-eval-ckad-sched-003-run-a`
**Fault:** `nodeSelector=k8s03`; taint `postops-test=true:NoSchedule`; không toleration

HolmesGPT xác định đúng `Pending`, `FailedScheduling`, taint không được tolerate và selector k8s03. Nó đề xuất thêm toleration hẹp hoặc gỡ constraint; không thực thi lệnh.

Telemetry: 13 tool calls; `prompt_tokens=36571`, `completion_tokens=1427`, `total_tokens=37998`; thời gian khoảng **1m16s**.

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
