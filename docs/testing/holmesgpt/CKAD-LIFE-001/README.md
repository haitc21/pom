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
| [Run A](run-a-holmesgpt.md) | Chỉ HolmesGPT, không Agent Memory | Đã hoàn tất | 88/100 | Đúng root cause và bằng chứng; có sai lệch nhỏ về Pod phase tại thời điểm trả lời |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + TencentDB Agent Memory | Chưa thực hiện | — | Chờ chạy cùng prompt, model và oracle tương đương Run A |

## So sánh cần thực hiện sau Run B

- Điểm Run B trừ điểm Run A.
- Thời gian tới giả thuyết đúng.
- Số tool call, token và thời gian phản hồi.
- Memory có truy hồi đúng case hay đưa vào thông tin không phù hợp.
- Khả năng giữ đúng namespace, Pod, image và điều kiện áp dụng.

