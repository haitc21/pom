# CKAD-LIFE-004 — Run A: HolmesGPT only

**Namespace:** `holmes-eval-ckad-life-004-run-a`
**Fault:** `livenessProbe.httpGet.path=/wrong-live` trên NGINX `1.27`

## Kết quả

HolmesGPT xác định đúng probe trả 404, kubelet restart container, và đề xuất đổi path thành `/`. Nó loại trừ OOM, image pull, crash ứng dụng và node issue bằng evidence hiện tại; không thực thi lệnh.

Telemetry: 11 tool calls; `prompt_tokens=19315`, `completion_tokens=1803`, `total_tokens=21118`; thời gian request khoảng **1m17s**.

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
