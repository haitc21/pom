# CKAD-LIFE-001 — CrashLoopBackOff do command/args

## Tình huống chuẩn

Deployment `ckad-life-001` trong namespace tạm thời được cấu hình để container `nginx` chạy command in lỗi thiếu `/etc/demo/app.yaml`, sau đó thoát với `exit 1`. Kubernetes liên tục khởi động lại container.

## Đáp án chuẩn

- Deployment không đạt `Available`.
- Pod/container không `Ready`, container ở `CrashLoopBackOff` hoặc `Error` và restart count tăng.
- Log có thông báo `fatal: configuration file /etc/demo/app.yaml not found`.
- Root cause là `command`/`args` ép container thoát với exit code `1`; không phải lỗi pull image, scheduling, OOM hay network.
- Remediation là xóa command/args bị inject hoặc khôi phục command chạy NGINX đúng.
- Recovery được xác minh bằng Deployment `Available`, Pod `Ready`, restart không tiếp tục tăng và log không còn lỗi.

## Tổng hợp theo lần chạy

| Lần chạy | Cấu hình | Kết quả | Điểm | Đánh giá |
|---|---|---|---:|---|
| [Run A](run-a-holmesgpt.md) | Chỉ HolmesGPT, không POM Memory | Đã hoàn tất | 88/100 | Đúng root cause và bằng chứng; có sai lệch nhỏ về Pod phase tại thời điểm trả lời |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + POM Memory (Mem0 OSS) | Đã hoàn tất | 100/100 | Mem0 recall đúng resolution đã duyệt; HolmesGPT xác minh độc lập bằng chứng hiện tại |

## So sánh sau Run B

- Run B đạt 100/100, cao hơn Run A 12 điểm; chưa đủ dữ liệu để kết luận về hiệu suất token/latency vì Run A chưa có cùng telemetry.
- Mem0 truy hồi đúng case và không gây anchoring sai trong exact recurrence.
- Các cohort paraphrase, analogous, cross-project và hard-negative sẽ được chạy ở các bài test tiếp theo.
- Khả năng giữ đúng namespace, Pod, image và điều kiện áp dụng.
