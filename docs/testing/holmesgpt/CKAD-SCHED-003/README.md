# CKAD-SCHED-003 — Taint thiếu toleration

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~1m16s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~1m13s |

Oracle: Pod có `nodeSelector=k8s03`, node `k8s03` có taint `postops-test=true:NoSchedule`, nhưng Pod không có toleration. Scheduler báo taint mismatch; affinity/selector và taint control-plane là các rào cản phụ.

Paired delta: `0`. Taint đã được gỡ sau cleanup và node vẫn `Ready`.
