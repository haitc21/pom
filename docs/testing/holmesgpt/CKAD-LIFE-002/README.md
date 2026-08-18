# CKAD-LIFE-002 — ImagePullBackOff do image tag không hợp lệ

## Tóm tắt

| Lần chạy | Phạm vi | Trạng thái | Điểm | Nhận xét |
|---|---|---|---:|---|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 86/100 | Đúng image reference, nhưng loại trừ DNS quá chắc chắn dù PoC đang offline registry |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + AIC Memory (Mem0 OSS) | Hoàn tất | 90/100 | Memory recall đúng resolution; vẫn lặp lại overclaim về DNS, chưa chứng minh cải thiện root cause |

## Oracle

Deployment `ckad-life-002` dùng `docker.io/library/nginx:99.99.99-postops-invalid` với `imagePullPolicy: Always`, được schedule trên `k8s03`. Pod không khởi động, `ErrImagePull` rồi `ImagePullBackOff`; Deployment có `0/1` available. Event hiện tại đồng thời cho thấy DNS tới Docker Hub của PoC không ổn định, vì vậy bằng chứng runtime không đủ để phân biệt tuyệt đối tag không tồn tại với registry/DNS không truy cập được.

Đáp án kiểm thử: image reference không hợp lệ/không khả dụng; cần thay bằng image tag đã được phê duyệt và xác minh Pod `Ready`. HolmesGPT phải nêu rõ giới hạn bằng chứng mạng thay vì khẳng định DNS chỉ là hậu quả.

## So sánh

- Run B recall được resolution Run A qua Mem0 (`retrieved_count=2`, top score `0.2574080986747504`) và vẫn kiểm tra namespace mới.
- Cả hai lần đều đưa remediation an toàn, không tự thực hiện lệnh.
- Run B tăng 4 điểm nhờ trạng thái và bằng chứng chi tiết hơn, nhưng chưa cho thấy memory giúp phân biệt nguyên nhân image với lỗi registry/DNS.
- Đây là bài kiểm thử image-pull và memory exact/analogous; cần giữ kết quả này như một hard-negative về overconfidence mạng cho các bài tiếp theo.

## Cleanup

Namespace Run A và Run B đã xóa; `k8s01`, `k8s02`, `k8s03` vẫn `Ready`, HolmesGPT vẫn `1/1`.
