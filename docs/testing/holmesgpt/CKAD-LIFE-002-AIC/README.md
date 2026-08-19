# CKAD-LIFE-002-AIC — Image pull failure cần điều tra lặp

## Môi trường

- Namespace: `holmes-eval-ckad-life-002-aic`
- Workload: `deployment/ckad-life-002`
- Fixture: `deploy/demo/test-fixtures/ckad-life-002-aic.yaml`
- Fault: Pod không khởi động; event runtime có cả lỗi pull image và lỗi DNS registry.

## Luồng chạy

1. Gửi symptom-only bằng curl lượt đầu; không đưa image tag hoặc đáp án vào prompt.
2. Đọc yêu cầu điều tra của HolmesGPT.
3. Kỹ sư tự chạy các lệnh read-only HolmesGPT yêu cầu.
4. Gửi nguyên văn command/output bằng curl lượt tiếp theo, giữ `conversation_id` và dùng `request_id` UUIDv7 mới.
5. Lặp đến khi HolmesGPT tách được điều đã chứng minh khỏi giả thuyết chưa đủ bằng chứng.

Không tự sửa Deployment trong quá trình đánh giá.
