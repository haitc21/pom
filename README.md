# AI Incident Copilot (AIC)

**AI Incident Copilot (AIC)** là đề xuất xây dựng nền tảng trí nhớ và hỗ trợ xử lý sự cố vận hành thông minh cho Phòng Điện toán đám mây – Trung tâm CNTT.

Giải pháp kết hợp:

- Redmine để định danh và quản lý sự cố.
- HolmesGPT để điều tra Kubernetes và Prometheus.
- PostgreSQL làm nguồn dữ liệu nghiệp vụ cho ticket, hội thoại, kết luận, phê duyệt và phiên bản Skill.
- Mem0 OSS làm lớp trích xuất và truy xuất ngữ nghĩa tùy chọn cho kinh nghiệm vận hành đã được xác nhận.
- LiteLLM làm cổng kết nối tới các mô hình AI triển khai on-premise.
- Quy trình để DevOps Engineer điều tra nhiều vòng, xác nhận câu trả lời cuối, rồi tạo, phê duyệt và tái sử dụng Skill.

AIC là trợ lý cho DevOps Engineer, không phải hệ thống tự động quyết định nguyên nhân. HolmesGPT có thể đưa ra giả thuyết chưa đầy đủ hoặc chưa đúng; kết luận của kỹ sư mới là dữ liệu chuẩn được lưu và tái sử dụng.

PoC tập trung vào Kubernetes với hai loại sự cố `CrashLoopBackOff` và `OOMKilled`.

Xem hồ sơ đầy đủ tại [Hồ sơ ý tưởng sáng kiến AI Incident Copilot (AIC)](outputs/ho-so-sang-kien-kho-ky-nang-xu-ly-su-co.md).
