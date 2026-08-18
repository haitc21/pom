# CKAD-LIFE-001 — Run A: HolmesGPT only

**Ngày chạy:** 2026-08-18  
**Mode:** HolmesGPT only; không truy hồi hoặc ghi AIC Memory
**Snapshot:** `poc-eval-20260818` trên cả 5 VM  
**Namespace:** `holmes-eval-ckad-life-001`

## Fault được tạo

Deployment sử dụng image đã có sẵn `docker.io/library/nginx:1.27`, với container command:

```sh
echo fatal: configuration file /etc/demo/app.yaml not found >&2; exit 1
```

Kết quả độc lập trước khi hỏi HolmesGPT:

- Deployment `ckad-life-001`: `0/1` available.
- Pod: không ready, restart count tăng, container vào `CrashLoopBackOff`/`Error`.
- Log: `fatal: configuration file /etc/demo/app.yaml not found`.
- Event: `Back-off restarting failed container`.
- Image đã có trên node và Pod đã được schedule thành công.

## Câu hỏi gửi HolmesGPT

Trong namespace `holmes-eval-ckad-life-001`, Deployment `ckad-life-001` đang gặp sự cố. Hãy điều tra chỉ bằng dữ liệu Kubernetes và Prometheus hiện tại. Trả lời bằng tiếng Việt, gồm: triệu chứng và trạng thái chính xác, nguyên nhân gốc có bằng chứng từ Pod events/logs/spec, các nguyên nhân đã loại trừ, remediation an toàn không tự thực hiện, và cách xác minh phục hồi.

## Kết quả HolmesGPT

HolmesGPT xác định:

- Deployment không khả dụng và container bị CrashLoopBackOff.
- `command`/`args` chứa lệnh in lỗi rồi thoát với `exit 1`.
- Bằng chứng phù hợp nằm trong Deployment spec, container log và `lastState.terminated.exitCode`.
- Image pull, scheduling/resource, NGINX và network không có bằng chứng là nguyên nhân.
- Remediation an toàn là xóa command/args bị inject hoặc khôi phục command chạy NGINX.
- Cách xác minh là kiểm tra Deployment available, Pod `Ready`, restart count và Events/logs.

## Đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Nhận diện triệu chứng/trạng thái | 8/10 |
| Root cause | 30/30 |
| Bằng chứng | 20/20 |
| Remediation | 15/15 |
| Xác minh phục hồi | 10/10 |
| Phạm vi/provenance | 5/5 |
| An toàn | 10/10 |
| Phạt sai lệch trạng thái tại thời điểm trả lời | -10 |
| **Tổng** | **88/100** |

### Nhận xét

Root cause và remediation đúng. HolmesGPT mô tả Pod phase là `Running` trong khi snapshot độc lập cuối cùng là phase `Error`; container state và CrashLoopBackOff vẫn được nhận diện chính xác. Đây là lỗi precision theo thời điểm, không phải lỗi chẩn đoán nguyên nhân.

## Cleanup

- Namespace test đã xóa và xác nhận không còn.
- Các node Kubernetes vẫn `Ready`.
- HolmesGPT, Prometheus, Grafana, Loki và Alertmanager vẫn hoạt động.
- Port-forward tạm thời đã dừng.
