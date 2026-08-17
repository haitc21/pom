# HỒ SƠ Ý TƯỞNG SÁNG KIẾN CNTT NĂM 2026

## 1. Thông tin sáng kiến

| Trường thông tin | Nội dung đề xuất |
|---|---|
| Tên sáng kiến | Xây dựng nền tảng trí nhớ vận hành và hỗ trợ xử lý sự cố bằng AI |
| Tên dự án tiếng Anh | **PostOps Memory** |
| Tên mô tả | **PostOps Memory – Nền tảng trí nhớ và hỗ trợ xử lý sự cố vận hành thông minh** |
| Đơn vị | Phòng Điện toán đám mây – Trung tâm CNTT |
| Phạm vi PoC | Kubernetes, Prometheus và ticket Redmine |
| Công nghệ chính | TencentDB Agent Memory, HolmesGPT và LiteLLM on-premise |

## 2. Tóm tắt ý tưởng

**PostOps Memory** là nền tảng tích lũy trí nhớ vận hành từ các sự cố thực tế, giúp AI tái sử dụng kinh nghiệm đã được kỹ sư xác nhận để hỗ trợ điều tra những sự cố tiếp theo.

Khi có ticket mới, giải pháp lấy nội dung từ Redmine, tìm các trường hợp và Skill tương tự trong TencentDB Agent Memory rồi cung cấp ngữ cảnh cho HolmesGPT. HolmesGPT truy vấn dữ liệu hiện tại từ Kubernetes và Prometheus ở chế độ chỉ đọc để đề xuất giả thuyết, bước kiểm tra, bằng chứng và hướng xử lý. Kỹ sư vận hành quyết định hành động, xác nhận nguyên nhân và đánh giá từng gợi ý.

Sau khi ticket hoàn tất, lịch sử điều tra, bằng chứng quan trọng, kết luận và phản hồi được lưu thành trí nhớ vận hành. Hệ thống tạo hoặc cập nhật Skill xử lý sự cố; Skill phải được con người phê duyệt trước khi cung cấp cho HolmesGPT.

Vòng lặp cải tiến:

**Ticket → Tìm kinh nghiệm → Điều tra → Kỹ sư xác nhận → Lưu trí nhớ → Tạo/cập nhật Skill → Phê duyệt → Tái sử dụng → Đánh giá và cải tiến.**

## 3. Hiện trạng và vấn đề cần giải quyết

- Kinh nghiệm xử lý sự cố phân tán trong ticket, trao đổi nội bộ, tài liệu rời rạc hoặc trí nhớ cá nhân.
- Khi sự cố tương tự tái diễn, kỹ sư phải lặp lại nhiều bước tra cứu log, metric, Kubernetes Events và tài liệu.
- Một sự cố có thể sinh nhiều alert và ảnh hưởng chuỗi dịch vụ phụ thuộc; alert không thể là mã định danh duy nhất của sự cố.
- Ticket đã đóng chưa tự động trở thành tài sản tri thức có cấu trúc và có thể tái sử dụng.
- AI tổng quát chưa hiểu đầy đủ kiến trúc, quy ước đặt tên và quy trình nội bộ của Tổng công ty.
- Khối lượng log và metric rất lớn; sao chép toàn bộ sang một Data Warehouse mới chỉ để phục vụ AI sẽ phức tạp và tốn kém.

## 4. Mục tiêu

### 4.1. Mục tiêu PoC

- Tích hợp Redmine với HolmesGPT mà không thay đổi quy trình ticket hiện tại.
- Hỗ trợ điều tra một số sự cố Kubernetes bằng dữ liệu trực tiếp từ Kubernetes và Prometheus.
- Cung cấp cho AI các sự cố, kinh nghiệm và Skill tương tự đã được xác nhận.
- Ghi nhận lựa chọn, kết quả thực hiện và đánh giá của kỹ sư.
- Tạo bản nháp Skill từ ticket đã xử lý và cho phép phê duyệt trước khi phát hành.
- Chứng minh khả năng giảm thời gian điều tra và chuẩn hóa quy trình xử lý sự cố.

### 4.2. Mục tiêu dài hạn

- Chuyển kinh nghiệm cá nhân thành tài sản tri thức vận hành của tổ chức.
- Hình thành bộ nhớ và bộ Skill đặc thù cho môi trường CNTT của Tổng công ty.
- Tạo dữ liệu có kiểm duyệt để cải thiện tìm kiếm, xếp hạng và huấn luyện model chuyên biệt trong tương lai.
- Mở rộng từ Kubernetes sang hệ thống log, Zabbix, OpenStack, VMware, database và middleware.

## 5. Nguyên tắc thiết kế

1. **Ticket là trung tâm:** Redmine ticket đại diện cho sự cố do con người xác nhận; alert chỉ là tín hiệu hoặc bằng chứng.
2. **Không sao chép toàn bộ telemetry:** Log và metric nằm tại hệ thống nguồn; chỉ lưu truy vấn, liên kết, kết quả quan trọng và bằng chứng đã chọn.
3. **AI chỉ đọc trong PoC:** HolmesGPT chỉ được cấp quyền đọc Kubernetes và Prometheus.
4. **Con người quyết định:** Kỹ sư xác nhận nguyên nhân, cách xử lý và phê duyệt Skill.
5. **Chỉ sử dụng tri thức đã duyệt:** Trí nhớ hoặc Skill chưa xác nhận không được coi là quy trình chính thức.
6. **Có thể truy vết:** Gợi ý phải chỉ ra ticket, Skill hoặc bằng chứng vận hành làm nguồn.
7. **PoC nhỏ nhưng mở rộng được:** Bắt đầu với một cluster và hai loại sự cố phổ biến.

## 6. Các thành phần giải pháp

### 6.1. Redmine – nguồn định danh sự cố

- Quản lý ticket, trạng thái, người phụ trách và trao đổi xử lý.
- Ticket ID liên kết nhiều alert, dịch vụ bị ảnh hưởng và dữ liệu điều tra vào cùng một sự cố.
- Nhận lại bản tóm tắt hoặc liên kết tới phiên điều tra trong PostOps Memory.

### 6.2. HolmesGPT – bộ máy điều tra sự cố

- Nhận nội dung ticket và kinh nghiệm/Skill liên quan.
- Truy vấn Kubernetes và Prometheus bằng công cụ thực tế ở chế độ chỉ đọc.
- Hình thành, kiểm chứng và loại trừ giả thuyết.
- Trình bày bằng chứng, hướng kiểm tra, đề xuất xử lý và cách xác nhận phục hồi.

### 6.3. TencentDB Agent Memory – nền tảng trí nhớ vận hành

- Lưu hội thoại, quá trình điều tra, lần gọi công cụ, kết luận và feedback.
- Trích xuất và tổ chức kinh nghiệm thành các lớp trí nhớ có thể tìm kiếm.
- Quản lý Skill, tài nguyên liên quan, phiên bản, quyền sở hữu và trạng thái.
- Tìm kiếm kết hợp từ khóa và ngữ nghĩa để đưa trường hợp phù hợp vào ngữ cảnh mới.
- Triển khai nội bộ để bảo vệ dữ liệu vận hành.

### 6.4. LiteLLM – cổng mô hình AI nội bộ

- Cung cấp API thống nhất cho HolmesGPT, Agent Memory và ứng dụng.
- Thực hiện định tuyến model, logging, rate limit và fallback.
- Không tự huấn luyện hoặc thay đổi trọng số model sau mỗi ticket.

### 6.5. PostOps Memory – lớp tích hợp và giao diện nghiệp vụ

- Đọc và liên kết ticket Redmine.
- Khởi tạo phiên điều tra HolmesGPT.
- Tìm và hiển thị trí nhớ/Skill tương tự từ TencentDB Agent Memory.
- Hiển thị giả thuyết, bằng chứng và đề xuất xử lý.
- Thu nhận kết luận và feedback của kỹ sư.
- Điều phối tạo, rà soát, phê duyệt và phát hành Skill.
- Chuyển đổi Skill sang `SKILL.md` nếu Agent Memory và HolmesGPT chưa tương thích trực tiếp.

## 7. Kiến trúc logic

```text
Người vận hành
      │
      ▼
PostOps Memory ─────────────── Redmine
      │
      ├── tìm/lưu trí nhớ ─── TencentDB Agent Memory
      │
      └── yêu cầu điều tra ── HolmesGPT
                                  │
                         Kubernetes / Prometheus

HolmesGPT và Agent Memory ───── LiteLLM ───── Model AI on-premise
```

HolmesGPT chuyên điều tra; TencentDB Agent Memory chuyên ghi nhớ; LiteLLM cung cấp model; Redmine quản lý sự cố; PostOps Memory điều phối quy trình nghiệp vụ.

## 8. Phạm vi PoC tối giản

- Một Kubernetes cluster thử nghiệm hoặc phạm vi production chỉ đọc.
- Hai loại sự cố: `CrashLoopBackOff` và `OOMKilled`.
- Khoảng 10–20 ticket hoặc kịch bản lịch sử đã được xác nhận.
- Dữ liệu Kubernetes và Prometheus; chưa thu thập toàn bộ log vào kho mới.
- Người dùng nhập Redmine ticket ID để bắt đầu điều tra.
- Skill phải được kỹ sư duyệt trước khi sử dụng lại.
- AI không tự thay đổi cấu hình hoặc khắc phục trên production.

## 9. Luồng hoạt động end-to-end

### Bước 1: Khởi tạo từ ticket

Kỹ sư nhập Redmine ticket ID và bổ sung cluster, namespace hoặc khoảng thời gian nếu ticket chưa có.

### Bước 2: Thu thập ngữ cảnh

PostOps Memory đọc tiêu đề, mô tả, bình luận và thông tin liên quan. Ticket ID là khóa liên kết giữa sự cố, nhiều alert và các dịch vụ bị ảnh hưởng.

### Bước 3: Tìm trí nhớ và Skill tương tự

Ứng dụng truy vấn TencentDB Agent Memory để tìm sự cố cũ, nguyên nhân, cách xử lý và Skill có điều kiện áp dụng phù hợp. Kỹ sư có thể chọn hoặc đánh dấu kết quả không liên quan.

### Bước 4: HolmesGPT điều tra

PostOps Memory gửi nội dung ticket, phạm vi, thời gian và trí nhớ liên quan cho HolmesGPT. HolmesGPT kiểm tra Pod, Deployment, Node, Kubernetes Events và metric Prometheus để xác nhận hoặc loại trừ giả thuyết.

### Bước 5: Trình bày kết quả có bằng chứng

Hệ thống hiển thị giả thuyết theo thứ tự ưu tiên, các bước đã kiểm tra, bằng chứng, nguyên nhân đã loại trừ, trường hợp tham khảo, hướng xử lý và cách xác nhận phục hồi.

### Bước 6: Kỹ sư xử lý và phản hồi

Kỹ sư chọn đề xuất phù hợp và đánh giá từng gợi ý theo các mức: hữu ích, không cần thiết, không phù hợp, không chính xác, có rủi ro hoặc thiếu bước quan trọng.

### Bước 7: Xác nhận kết quả thực tế

Kỹ sư xác nhận nguyên nhân gốc, cách khắc phục, cách kiểm tra phục hồi và kết quả cuối cùng. Đây là dữ liệu chuẩn để cải thiện hệ thống.

### Bước 8: Ghi nhớ kinh nghiệm

PostOps Memory gửi phiên điều tra, bằng chứng quan trọng, kết luận và feedback vào TencentDB Agent Memory. Chỉ lưu truy vấn, kết quả chọn lọc và tham chiếu; không lưu toàn bộ telemetry.

### Bước 9: Tạo hoặc cập nhật Skill

Hệ thống tạo bản nháp Skill gồm điều kiện kích hoạt, dữ liệu cần kiểm tra, trình tự điều tra, cách diễn giải, cảnh báo an toàn, hướng xử lý và cách xác nhận phục hồi.

### Bước 10: Phê duyệt và phát hành

Kỹ sư rà soát, sửa và phê duyệt Skill. PostOps Memory xuất hoặc chuyển đổi Skill sang `SKILL.md`, sau đó cung cấp cho HolmesGPT và quản lý theo phiên bản.

### Bước 11: Tái sử dụng và cải tiến

Ở ticket tiếp theo, Agent Memory truy xuất kinh nghiệm liên quan và HolmesGPT sử dụng Skill phù hợp. Feedback mới tiếp tục cải thiện tìm kiếm, nội dung Skill và thứ tự gợi ý.

## 10. Cấu trúc trí nhớ vận hành tối thiểu

- Redmine ticket ID và tiêu đề.
- Dịch vụ bị ảnh hưởng, cluster và namespace.
- Thời gian bắt đầu, phát hiện, xử lý và phục hồi.
- Alert hoặc triệu chứng liên quan.
- Các giả thuyết đã kiểm tra và kết quả.
- Truy vấn/tool quan trọng cùng bằng chứng chọn lọc.
- Nguyên nhân gốc đã xác nhận.
- Cách xử lý thực tế và cách xác nhận phục hồi.
- Skill đã sử dụng, phiên bản và mức hữu ích.
- Nội dung kỹ sư sửa hoặc bổ sung.
- Người xác nhận và trạng thái kiểm duyệt.

## 11. Cơ chế để AI ngày càng hữu ích hơn

### Cấp độ 1 – Trí nhớ sự cố

Ticket đã xử lý cung cấp ngữ cảnh cho ticket mới. AI ưu tiên giả thuyết từng xảy ra trong môi trường nội bộ nhưng vẫn phải kiểm chứng trên dữ liệu hiện tại.

### Cấp độ 2 – Skill vận hành

Kinh nghiệm được chuyển thành quy trình có cấu trúc, có phiên bản và phê duyệt. Đây là cách cải thiện nhanh, dễ kiểm toán và không cần huấn luyện lại model.

### Cấp độ 3 – Học từ phản hồi

Lựa chọn của kỹ sư tạo dữ liệu về trường hợp tương tự đúng/sai, Skill hữu ích/không phù hợp và gợi ý chính xác/rủi ro. Dữ liệu được dùng để cải thiện truy xuất và xếp hạng.

### Cấp độ 4 – Model chuyên biệt theo tác vụ

Khi có đủ dữ liệu chất lượng, có thể fine-tune model nhỏ cho phân loại ticket, xác định phạm vi, xếp hạng nguyên nhân hoặc tạo Skill. Model được triển khai sau LiteLLM và chỉ sử dụng khi vượt bộ đánh giá chuẩn.

AI không tự thay đổi trọng số sau mỗi sự cố. Hệ thống hữu ích hơn trước tiên nhờ trí nhớ, Skill và feedback; fine-tuning chỉ thực hiện khi đã có dữ liệu đủ tốt.

## 12. Roadmap triển khai

### Giai đoạn 0 – Chuẩn bị PoC (1–2 tuần)

- Triển khai HolmesGPT và kết nối LiteLLM.
- Triển khai TencentDB Agent Memory on-premise.
- Cấp quyền chỉ đọc cho Kubernetes và Prometheus.
- Chọn một cluster, hai loại sự cố và 10–20 ticket/kịch bản mẫu.
- Kiểm chứng API, khả năng lưu phiên điều tra và cơ chế xuất/chuyển đổi Skill.

### Giai đoạn 1 – PoC vòng lặp trí nhớ (3–6 tuần)

- Xây giao diện PostOps Memory đọc ticket Redmine theo ID.
- Tích hợp truy xuất trí nhớ từ TencentDB Agent Memory.
- Gọi HolmesGPT qua HTTP API và hiển thị báo cáo có bằng chứng.
- Thu nhận kết luận và feedback của kỹ sư.
- Lưu phiên xử lý thành trí nhớ vận hành.
- Tạo, chỉnh sửa, phê duyệt và xuất `SKILL.md`.
- Chứng minh Skill được tái sử dụng trong sự cố tiếp theo.

### Giai đoạn 2 – Mở rộng và nâng chất lượng (3–6 tháng)

- Đồng bộ Redmine qua webhook và ghi kết quả trở lại ticket.
- Bổ sung Loki/OpenSearch, lịch sử triển khai và Zabbix.
- Mở rộng loại sự cố và số lượng Skill.
- Cải thiện xếp hạng bằng feedback và xây bộ đánh giá từ ticket đã xác nhận.

### Giai đoạn 3 – AI chuyên biệt và đa nền tảng (6–12 tháng)

- Chuẩn hóa, ẩn dữ liệu nhạy cảm và tạo tập train/validation/test.
- Thử nghiệm model nhỏ cho tác vụ hẹp và đưa qua LiteLLM nếu đạt KPI.
- Mở rộng sang OpenStack, VMware, database, storage và middleware.

## 13. Chỉ số đánh giá PoC

- Thời gian đến giả thuyết hữu ích đầu tiên, thời gian xác định nguyên nhân và MTTR.
- Tỷ lệ tìm đúng sự cố tương tự trong Top 3.
- Tỷ lệ HolmesGPT chọn đúng Skill.
- Tỷ lệ gợi ý được đánh giá hữu ích, sai hoặc có rủi ro.
- Thời gian tạo hồ sơ hậu kiểm và bản nháp Skill.
- Tỷ lệ Skill được duyệt và tái sử dụng thành công.
- Số bước tra cứu thủ công được giảm.

Mục tiêu tham khảo:

- Giảm tối thiểu 30% thời gian xác định nguyên nhân với kịch bản đã có Skill.
- Ít nhất 70% bước gợi ý được đánh giá đúng hoặc hữu ích.
- 100% Skill được con người phê duyệt trước khi phát hành.
- 100% kết nối Kubernetes trong PoC sử dụng quyền chỉ đọc.
- Giảm tối thiểu 50% thời gian tạo bản nháp hướng dẫn sau sự cố.

## 14. Giá trị mang lại

### Giá trị vận hành

- Rút ngắn thời gian thu thập thông tin và kiểm chứng giả thuyết.
- Giảm tra cứu lặp lại, hỗ trợ kỹ sư mới và chuẩn hóa hậu kiểm.
- Tăng khả năng tái sử dụng kinh nghiệm đã xác nhận.

### Giá trị tổ chức

- Giảm phụ thuộc vào tri thức của một số cá nhân.
- Biến ticket đã đóng thành tài sản có thể tìm kiếm, phiên bản hóa và kiểm toán.
- Tạo nền tảng dữ liệu được kiểm duyệt cho AI chuyên biệt sau này.

### Giá trị đầu tư

- Tận dụng Redmine, Kubernetes, Prometheus và LiteLLM hiện có.
- Sử dụng HolmesGPT và TencentDB Agent Memory theo hướng mã nguồn mở, on-premise.
- Không cần xây Data Warehouse lưu toàn bộ log/metric hoặc huấn luyện model trong PoC.
- Kiểm chứng giá trị trên phạm vi nhỏ trước khi mở rộng.

## 15. Rủi ro và biện pháp kiểm soát

| Rủi ro | Biện pháp kiểm soát |
|---|---|
| AI kết luận sai | Bắt buộc có bằng chứng; kỹ sư xác nhận nguyên nhân cuối cùng |
| Trí nhớ sai ảnh hưởng lần sau | Chỉ dùng nội dung đã xác nhận; lưu nguồn, người duyệt và phiên bản |
| Skill tạo từ cách xử lý tình thế | Rà soát, giới hạn phạm vi và phê duyệt trước khi phát hành |
| Đề xuất hành động nguy hiểm | PoC chỉ đọc; Skill nêu hành động bị cấm và điều kiện chuyển cấp |
| Ticket thiếu thông tin | Cho phép bổ sung cluster, namespace và khoảng thời gian |
| Truy xuất nhầm sự cố | Hiển thị nguồn; kỹ sư chọn hoặc từ chối kết quả |
| Dữ liệu nhạy cảm đi vào prompt | On-premise, che dữ liệu nhạy cảm và áp dụng retention |
| Agent Memory chưa xuất trực tiếp định dạng HolmesGPT | PostOps Memory chuyển đổi sang `SKILL.md` |
| Telemetry quá lớn | Truy vấn tại nguồn, giới hạn thời gian và chỉ lưu bằng chứng cần thiết |

## 16. Phân tích theo sáu chiếc mũ tư duy

### Mũ trắng – Dữ kiện

- Đơn vị đã có Redmine, Kubernetes, Prometheus và LiteLLM on-premise.
- HolmesGPT có khả năng điều tra Kubernetes/Prometheus và dùng Skill tùy chỉnh.
- TencentDB Agent Memory cung cấp nền tảng lưu và truy xuất trí nhớ AI Agent.
- PoC không cần lưu toàn bộ telemetry hoặc fine-tune model.

### Mũ đỏ – Cảm nhận

- Kỹ sư có thể lo ngại phải nhập thêm dữ liệu hoặc bị AI thay thế.
- Giao diện cần tận dụng ticket sẵn có, giảm thao tác và khẳng định AI chỉ hỗ trợ.
- Bằng chứng và nguồn tham chiếu rõ ràng giúp tăng niềm tin.

### Mũ đen – Rủi ro

- Ticket hoặc kết luận có thể thiếu chính xác.
- AI có thể truy xuất sai kinh nghiệm hoặc suy diễn quá mức.
- Skill sai sẽ ảnh hưởng các lần xử lý sau.
- Khả năng chuyển đổi Skill giữa Agent Memory và HolmesGPT cần được kiểm chứng.

### Mũ vàng – Lợi ích

- PoC nhỏ nhưng tạo vòng lặp giá trị hoàn chỉnh.
- Kinh nghiệm tiếp tục được tích lũy sau khi đóng ticket.
- Tận dụng hạ tầng hiện có và ưu tiên mã nguồn mở on-premise.

### Mũ xanh lá – Sáng tạo

- Kết hợp điều tra thời gian thực với trí nhớ sự cố đã xác nhận.
- Chuyển phiên xử lý thành Skill có cấu trúc và phê duyệt.
- Dùng feedback từng gợi ý để cải thiện truy xuất và tạo dữ liệu tương lai.
- Xây kho “bằng chứng và kinh nghiệm” thay vì kho telemetry khổng lồ.

### Mũ xanh dương – Điều hành

- Bắt đầu với hai loại sự cố và 10–20 trường hợp mẫu.
- Giới hạn AI ở quyền chỉ đọc và yêu cầu phê duyệt Skill.
- Đo KPI trước/sau; chỉ mở rộng khi đạt ngưỡng hiệu quả và an toàn.

## 17. Điểm mới của sáng kiến

Điểm mới không nằm ở một chatbot riêng lẻ. PostOps Memory xây dựng vòng đời trí nhớ vận hành khép kín:

- Redmine định danh sự cố thực tế.
- HolmesGPT điều tra dữ liệu hiện tại.
- TencentDB Agent Memory lưu và truy xuất kinh nghiệm đã xác nhận.
- PostOps Memory thu nhận lựa chọn và feedback của kỹ sư.
- Kinh nghiệm được chuẩn hóa thành Skill, phê duyệt và tái sử dụng.
- Dữ liệu sử dụng tiếp tục cải thiện tìm kiếm, xếp hạng và chất lượng Skill.

AI ngày càng phù hợp với môi trường của Tổng công ty thông qua cơ chế học hỏi có kiểm soát, truy vết được và không phụ thuộc vào huấn luyện lại model ngay từ đầu.

## 18. Kết luận và đề xuất

Đề xuất triển khai PoC **PostOps Memory** trong 1–2 tháng với một Kubernetes cluster, hai loại sự cố `CrashLoopBackOff` và `OOMKilled`, cùng 10–20 ticket hoặc kịch bản đã xác nhận.

PoC cần chứng minh ba năng lực:

1. HolmesGPT điều tra ticket bằng dữ liệu Kubernetes và Prometheus thực tế.
2. TencentDB Agent Memory lưu và truy xuất đúng kinh nghiệm xử lý liên quan.
3. Kinh nghiệm được chuyển thành Skill, phê duyệt và tái sử dụng để nâng chất lượng xử lý sự cố tiếp theo.

Nếu đạt KPI, giải pháp được mở rộng tuần tự sang hệ thống log, Zabbix, OpenStack, VMware và các nền tảng nghiệp vụ; đồng thời sử dụng feedback để cải thiện xếp hạng và xây model chuyên biệt trong tương lai.
