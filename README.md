# PostOps Memory

**PostOps Memory** là đề xuất xây dựng nền tảng trí nhớ và hỗ trợ xử lý sự cố vận hành thông minh cho Phòng Điện toán đám mây – Trung tâm CNTT.

Giải pháp kết hợp:

- Redmine để định danh và quản lý sự cố.
- HolmesGPT để điều tra Kubernetes và Prometheus.
- TencentDB Agent Memory để lưu trữ và tái sử dụng kinh nghiệm vận hành.
- LiteLLM làm cổng kết nối tới các mô hình AI triển khai on-premise.
- Quy trình tạo, phê duyệt và tái sử dụng Skill từ các sự cố đã xử lý.

PoC tập trung vào Kubernetes với hai loại sự cố `CrashLoopBackOff` và `OOMKilled`.

Xem hồ sơ đầy đủ tại [Hồ sơ ý tưởng sáng kiến PostOps Memory](outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md).
