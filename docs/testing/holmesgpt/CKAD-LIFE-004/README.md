# CKAD-LIFE-004 — Liveness probe thất bại

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian HolmesGPT |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~1m17s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + POM Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~2m23s |

Oracle: NGINX đang chạy nhưng liveness probe `GET /wrong-live` trả 404. Kubelet phát event `Unhealthy` và `Killing`, restart count tăng. Đáp án là sửa probe path về `/` hoặc health path hợp lệ; không phải lỗi ứng dụng, OOM hay image.

Run B recall đúng resolution đã duyệt và không làm thay đổi chẩn đoán. Paired delta: `0`.

Namespace hai lần chạy đã cleanup; node và HolmesGPT vẫn healthy.
