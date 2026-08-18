# CKAD-LIFE-003 — Run B: HolmesGPT + POM Memory (Mem0 OSS)

**Ngày chạy:** 2026-08-18
**Mode:** HolmesGPT + POM Memory (Mem0 OSS)
**Namespace:** `holmes-eval-ckad-life-003-run-b`
**Memory data:** `/data/k8s-poc/mem0/data/ckad-life-003`

## Memory và fault

Resolution Run A được seed bằng `infer=False`: Pod Running nhưng NotReady do readiness probe `/wrong-ready` trả 404 và Service không có ready endpoint. Mem0 recall một record (`score=0.2574080986747504`), được chèn dưới nhãn tham khảo không quyết định.

Namespace mới dùng cùng fault, với Pod `Running`, `Ready=False`, event readiness HTTP 404 và Service Endpoints rỗng.

## Kết quả HolmesGPT

HolmesGPT kiểm chứng độc lập và xác định đúng chuỗi probe 404 → Pod NotReady → Service không có endpoint. Remediation đổi path probe thành `/`; đề xuất xác minh Pod Ready, endpoint và HTTP 200. Không lệnh nào được thực thi.

Telemetry: 15 tool calls; `prompt_tokens=48257`, `completion_tokens=2098`, `total_tokens=50355`; thời gian xử lý từ log request đến HTTP 200 khoảng **1m50s**.

## Chấm điểm

| Tiêu chí | Điểm |
|---|---:|
| Nhận diện triệu chứng/trạng thái | 10/10 |
| Root cause | 30/30 |
| Bằng chứng | 20/20 |
| Remediation | 15/15 |
| Xác minh phục hồi | 10/10 |
| Phạm vi/provenance | 5/5 |
| An toàn | 10/10 |
| **Tổng** | **100/100** |

Paired delta so với Run A: **0 điểm**. Bài test cho thấy memory không cải thiện điểm khi HolmesGPT đã đủ khả năng chẩn đoán từ evidence hiện tại.

## Cleanup

Namespace đã xóa và xác nhận không còn; các node vẫn `Ready`, HolmesGPT vẫn `1/1`. Raw response và Mem0 data nằm ngoài Git.
