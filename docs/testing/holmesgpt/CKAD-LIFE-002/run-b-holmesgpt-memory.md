# CKAD-LIFE-002 — Run B: HolmesGPT + AIC Memory (Mem0 OSS)

**Ngày chạy:** 2026-08-18
**Mode:** HolmesGPT + AIC Memory (Mem0 OSS)
**Namespace:** `holmes-eval-ckad-life-002-run-b`
**Memory data:** `/data/k8s-poc/mem0/data/ckad-life-002`

## Memory và fault

Resolution Run A được kỹ sư phê duyệt và seed bằng `infer=False`, chỉ chứa kết luận image reference không hợp lệ/không khả dụng, bằng chứng `ErrImagePull`/`ImagePullBackOff`, và cách phục hồi. Mem0 trả về `retrieved_count=2`, record đầu `4edb8307-550a-4530-9cbf-338494ef5598`, score `0.2574080986747504`. Nội dung được chèn dưới nhãn tham khảo không quyết định.

Namespace mới dùng cùng fault: `docker.io/library/nginx:99.99.99-postops-invalid`, Pod schedule trên `k8s03`, `ImagePullBackOff`, `0/1` available. Event vẫn đồng thời chứa lỗi DNS registry của môi trường PoC.

## Kết quả HolmesGPT

HolmesGPT xác minh đúng image tag, trạng thái Pod/Deployment, không có runtime log, và đề xuất đổi sang tag immutable đã phê duyệt. Câu trả lời vẫn khẳng định lỗi DNS là hậu quả của image không tồn tại và loại trừ lỗi mạng, nên memory chưa giúp giảm anchoring hoặc overconfidence. Không lệnh nào được thực thi.

Telemetry: 20 tool calls; `prompt_tokens=41604`, `completion_tokens=2187`, `total_tokens=43791`; `finish_reason=stop`.

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
| Phạt overclaim/loại trừ DNS không đủ bằng chứng | -10 |
| **Tổng** | **90/100** |

Paired delta so với Run A: **+4 điểm**. Delta nhỏ và không đủ để kết luận Mem0 cải thiện khả năng chẩn đoán; memory chủ yếu củng cố đúng giả thuyết đã seed.

## Cleanup

Namespace đã xóa và xác nhận không còn; các node vẫn `Ready`, HolmesGPT vẫn `1/1`. Raw response và Mem0 data nằm ngoài Git.
