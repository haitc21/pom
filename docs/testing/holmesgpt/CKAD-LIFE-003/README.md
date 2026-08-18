# CKAD-LIFE-003 — Pod Running nhưng không Ready do readiness probe

## Tóm tắt

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian HolmesGPT |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 100/100 | ~1m35s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~1m50s |

## Oracle

Pod NGINX `Running` nhưng `Ready=False` vì readiness probe HTTP gọi `/wrong-ready`, nhận HTTP 404. Service selector khớp Pod nhưng không có ready endpoint, nên traffic không được định tuyến. Đáp án là sửa probe về path hợp lệ như `/`, sau đó xác minh Pod `Ready` và EndpointSlice có endpoint.

## So sánh

- Run A và Run B đều xác định đúng chuỗi: probe 404 → Pod NotReady → Service không có endpoint.
- Run B recall đúng một resolution đã duyệt (`score=0.2574080986747504`) và vẫn kiểm tra bằng chứng namespace hiện tại.
- Không ghi nhận hallucination hoặc remediation nguy hiểm; cả hai đều không tự thực thi lệnh.

## Cleanup

Namespace Run A và Run B đã xóa; các node vẫn `Ready`, HolmesGPT vẫn `1/1`.
