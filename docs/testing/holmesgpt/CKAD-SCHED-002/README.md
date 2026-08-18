# CKAD-SCHED-002 — Node affinity không khớp node

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~1m13s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~0m59s |

Oracle: required nodeAffinity yêu cầu `kubernetes.io/hostname=node-that-does-not-exist`; scheduler báo hai node không match affinity và control-plane taint là rào cản phụ. Cả hai Run xác định đúng và đề xuất sửa/xóa affinity.

Paired delta: `0`.
