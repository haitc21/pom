# CKAD-LIFE-005 — OOMKilled do memory limit thấp

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian HolmesGPT |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~1m20s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~1m41s |

Oracle: command `awk` tạo allocation vượt memory limit `16Mi`; container bị `OOMKilled`, exit code 137, restart/backoff tăng. Đáp án là tăng limit theo usage đo được hoặc bỏ allocation giả lập.

Run B recall đúng resolution Run A; paired delta `0`.

Namespace đã cleanup; các node vẫn `Ready`.
