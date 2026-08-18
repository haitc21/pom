# CKAD-LIFE-002 — Run A: HolmesGPT only

**Ngày chạy:** 2026-08-18
**Mode:** HolmesGPT only; không truy hồi POM Memory
**Namespace:** `holmes-eval-ckad-life-002-run-a`
**Snapshot:** `poc-eval-20260818`

## Fault và oracle

Deployment có một container NGINX dùng image `docker.io/library/nginx:99.99.99-postops-invalid`, `imagePullPolicy: Always`, node selector `k8s03`. Pod được schedule nhưng không khởi động:

- Deployment: `0/1` available, `MinimumReplicasUnavailable`.
- Pod: `ErrImagePull`, sau đó `ImagePullBackOff`, phase `Pending`.
- Event: `Failed to pull image`, lỗi DNS `registry-1.docker.io`, rồi `Back-off pulling image`.
- Không có runtime log vì container chưa start.

Câu hỏi không tiết lộ image tag hoặc nguyên nhân; yêu cầu HolmesGPT nêu triệu chứng, root cause, bằng chứng, loại trừ, remediation an toàn và cách xác minh.

## Kết quả

HolmesGPT xác định đúng image reference `99.99.99-postops-invalid` là nguyên nhân trực tiếp, đề xuất thay bằng tag hợp lệ/immutable và kiểm tra Deployment, Pod, Events. Tuy nhiên, câu trả lời khẳng định lỗi DNS là hậu quả của tag không tồn tại và loại trừ lỗi mạng. Đây là kết luận vượt quá bằng chứng vì cluster PoC hiện không có đường DNS/egress ổn định tới Docker Hub.

Telemetry: 13 tool calls; `prompt_tokens=49908`, `completion_tokens=1777`, `total_tokens=51685`; `finish_reason=stop`.

## Chấm điểm

| Tiêu chí | Điểm |
|---|---:|
| Nhận diện triệu chứng/trạng thái | 10/10 |
| Root cause | 30/30 |
| Bằng chứng | 18/20 |
| Remediation | 15/15 |
| Xác minh phục hồi | 10/10 |
| Phạm vi/provenance | 5/5 |
| An toàn | 10/10 |
| Phạt overclaim/loại trừ DNS không đủ bằng chứng và remediation phụ không cần thiết | -12 |
| **Tổng** | **86/100** |

Đây là lỗi chẩn đoán phụ về mức độ chắc chắn, không phải nhầm root cause chính.

## Cleanup

Namespace đã xóa và xác nhận không còn; không sửa workload hay hạ tầng PoC.
