# CKAD-CONF-002 — Secret thiếu key

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 95/100 | ~2m05s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~2m20s |

Oracle: Secret `app-secret` tồn tại nhưng chỉ có `EXISTING_KEY`; Deployment dùng `secretKeyRef.key=MISSING_KEY`, tạo `CreateContainerConfigError` với Event `couldn't find key MISSING_KEY in Secret .../app-secret`.

Paired delta: `+5`. Run A xác định đúng root cause nhưng mô tả trạng thái Deployment có một câu mâu thuẫn (`Available` dù `availableReplicas=0`) và nói không thể kiểm tra Secret; Run B trình bày nhất quán hơn.
