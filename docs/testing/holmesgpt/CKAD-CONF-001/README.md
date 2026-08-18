# CKAD-CONF-001 — Thiếu ConfigMap được tham chiếu

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~2m05s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~2m00s |

Oracle: `envFrom.configMapRef.name=missing-config` nhưng ConfigMap không tồn tại trong namespace, khiến container ở `CreateContainerConfigError`; Event ghi `configmap "missing-config" not found`. Pod đã được schedule và image đã pull thành công.

Paired delta: `0`. Memory củng cố đúng giả thuyết và HolmesGPT vẫn kiểm chứng bằng spec, events và container state hiện tại.
