# HolmesGPT Evaluation Results

Bảng tổng hợp các bài test đánh giá độ chính xác và hiệu quả của HolmesGPT trong Kubernetes PoC.

| Tình huống | HolmesGPT | HolmesGPT + POM Memory | Thời gian thực hiện | Đáp án |
|---|---|---|---|---|
| [CKAD-LIFE-001 — CrashLoopBackOff do command/args làm container thoát](CKAD-LIFE-001/) | [Đã chạy — 88/100](CKAD-LIFE-001/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-LIFE-001/run-b-holmesgpt-memory.md) | Chưa đo đồng nhất | Container thoát với `exit 1` vì command/args cấu hình lỗi; cần khôi phục command chạy ứng dụng |
| [CKAD-LIFE-002 — ImagePullBackOff do image tag không hợp lệ](CKAD-LIFE-002/) | [Đã chạy — 86/100](CKAD-LIFE-002/run-a-holmesgpt.md) | [Đã chạy — 90/100](CKAD-LIFE-002/run-b-holmesgpt-memory.md) | Run A: ~1m45s; Run B: ~1m58s | Image reference không hợp lệ/không khả dụng; thay bằng tag đã phê duyệt và xác minh Pod Ready |
| [CKAD-LIFE-003 — Pod Running nhưng không Ready do readiness probe](CKAD-LIFE-003/) | [Đã chạy — 100/100](CKAD-LIFE-003/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-LIFE-003/run-b-holmesgpt-memory.md) | Run A: ~1m35s; Run B: ~1m50s | Readiness probe `/wrong-ready` trả 404; sửa về path hợp lệ để Pod Ready và Service có endpoint |
| [CKAD-LIFE-004 — Liveness probe thất bại](CKAD-LIFE-004/) | [Đã chạy — 100/100](CKAD-LIFE-004/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-LIFE-004/run-b-holmesgpt-memory.md) | Run A: ~1m17s; Run B: ~2m23s | Liveness probe `/wrong-live` trả 404 khiến kubelet restart container; sửa path probe |
| [CKAD-LIFE-005 — OOMKilled do memory limit thấp](CKAD-LIFE-005/) | [Đã chạy — 100/100](CKAD-LIFE-005/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-LIFE-005/run-b-holmesgpt-memory.md) | Run A: ~1m20s; Run B: ~1m41s | Command vượt memory limit 16Mi; container bị OOMKilled/exit 137 |
| [CKAD-SCHED-001 — CPU request vượt allocatable](CKAD-SCHED-001/) | [Đã chạy — 70/100](CKAD-SCHED-001/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-SCHED-001/run-b-holmesgpt-memory.md) | Run A: ~1m22s; Run B: ~1m08s | `cpu: "100"` là 100 cores, vượt 2 cores/node; scheduler báo `Insufficient cpu` |
| [CKAD-SCHED-002 — Node affinity không khớp node](CKAD-SCHED-002/) | [Đã chạy — 100/100](CKAD-SCHED-002/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-SCHED-002/run-b-holmesgpt-memory.md) | Run A: ~1m13s; Run B: ~0m59s | Affinity yêu cầu hostname không tồn tại; sửa/xóa constraint để Pod được schedule |
| [CKAD-SCHED-003 — Taint thiếu toleration](CKAD-SCHED-003/) | [Đã chạy — 100/100](CKAD-SCHED-003/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-SCHED-003/run-b-holmesgpt-memory.md) | Run A: ~1m16s; Run B: ~1m13s | `k8s03` có taint `NoSchedule`, Pod thiếu toleration; thêm toleration hẹp hoặc rollback taint |
| [CKAD-CONF-001 — Thiếu ConfigMap được tham chiếu](CKAD-CONF-001/) | [Đã chạy — 100/100](CKAD-CONF-001/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-CONF-001/run-b-holmesgpt-memory.md) | Run A: ~2m05s; Run B: ~2m00s | `envFrom` tham chiếu `missing-config` không tồn tại, gây `CreateContainerConfigError`; tạo/khôi phục ConfigMap hoặc bỏ tham chiếu sau khi duyệt |
| [CKAD-CONF-002 — Secret thiếu key](CKAD-CONF-002/) | [Đã chạy — 95/100](CKAD-CONF-002/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-CONF-002/run-b-holmesgpt-memory.md) | Run A: ~2m05s; Run B: ~2m20s | `secretKeyRef` dùng `MISSING_KEY` không tồn tại trong `app-secret`; khôi phục key hoặc sửa tham chiếu sau khi duyệt |
| [CKAD-CONF-003 — Ghi đè command/args sai](CKAD-CONF-003/) | [Đã chạy — 95/100](CKAD-CONF-003/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-CONF-003/run-b-holmesgpt-memory.md) | Run A: ~2m05s; Run B: ~2m20s | `exec /missing/start` không tồn tại, exit 127 và BackOff; xóa command/args hoặc sửa command hợp lệ |

## Round 2 — iterative human-in-the-loop

| Test/Run | Round 1 | Round 2 | Số vòng | Ghi chú |
|---|---:|---:|---:|---|
| [CKAD-LIFE-001 Run A](CKAD-LIFE-001/run-a-r2-iterative.md) | 88/100 | **100/100** | 4 | HolmesGPT yêu cầu lệnh; kỹ sư gửi output, phát hiện `set image` không xóa command/args, sau đó patch và xác minh rollout |
| [CKAD-LIFE-002 Run A](CKAD-LIFE-002/run-a-r2-iterative.md) | 86/100 | 85/100 | 4 | Iteration xác nhận DNS/egress lỗi; vẫn còn overclaim rằng image tag có/không tồn tại khi registry không reachable |
| [CKAD-LIFE-002 Run B](CKAD-LIFE-002/run-b-r2-iterative.md) | 90/100 | **100/100** | 3 | Memory gợi ý kiểm tra; output `docker pull not found` buộc HolmesGPT tách tag invalid khỏi DNS node |
| [CKAD-LIFE-001 Run B](CKAD-LIFE-001/run-b-r2-iterative.md) | 100/100 | **100/100** | 3 | Chạy lại do test có Run A dưới 100; memory được kiểm chứng, remediation xóa command/args và rollout thành công |

## Quy ước

- `run-a-holmesgpt.md`: lần chạy chỉ dùng HolmesGPT, không có bộ nhớ được truy hồi.
- `run-b-holmesgpt-memory.md`: lần chạy HolmesGPT có POM Memory triển khai bằng Mem0 OSS và resolution đã duyệt.
- Điểm hiện tại là điểm provisional theo rubric trong [thiết kế đánh giá](../holmesgpt-memory-evaluation.md).
- Thời gian là end-to-end từ log `Received: /api/chat request` đến log HTTP 200, chỉ tính thời gian HolmesGPT xử lý; chưa bao gồm dựng fault, cleanup hoặc thời gian Mem0 seed.
- Run B đã được chạy và chấm độc lập; các cohort paraphrase, analogous và hard-negative đầy đủ vẫn chưa chạy. CKAD-LIFE-002 cho thấy cần chấm riêng lỗi overconfidence khi registry/DNS cũng có thể gây cùng triệu chứng.
