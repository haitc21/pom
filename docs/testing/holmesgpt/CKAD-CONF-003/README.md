# CKAD-CONF-003 — Ghi đè command/args sai

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 95/100 | ~2m05s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~2m20s |

Oracle: `command: /bin/sh -c` và `args: exec /missing/start` ghi đè entrypoint nginx; file không tồn tại, log báo `not found`, exit code 127 và Pod bị BackOff/CrashLoopBackOff.

Paired delta: `+5`. Run A chẩn đoán đúng nhưng nêu một ví dụ `args` không phù hợp khi vẫn giữ `/bin/sh -c`; Run B đưa remediation hợp lệ và bám sát memory đã duyệt.
