# AIC-MEMORY-NGINX-CONFIG — NGINX ConfigMap rollout crash

Ngày chạy: 2026-08-19.

## Mục tiêu

Đánh giá Memory của AIC với một lỗi cấu hình gần production: rollout ConfigMap
làm NGINX crash, làm Deployment unavailable và Service không có ready backend.
Memory không được phép thay thế bằng chứng của incident hiện hành.

## Thiết lập

- Fixture: `deploy/demo/test-fixtures/aic-nginx-config-crashloop.yaml`
- Incident hiện hành: `INC-2026-0819-EDGE`
- Namespace: `holmes-eval-aic-nginx-config-current`
- Workload: `deployment/edge-gateway`, hai replicas.
- Fault: `default.conf` mount từ ConfigMap thiếu `;` sau lệnh `return`.

Memory lịch sử được tạo qua API từ incident khác, `INC-2026-0412`:

| Trường | Giá trị |
|---|---|
| Resolution | `inc-2026-0412-nginx-config-crashloop-v1` |
| Memory ID | `2bdb063c-2076-4b60-949b-afa6822c66c3` |
| Signature | `container_crash` / `CrashLoopBackOff` / `Pod` |
| Nội dung | symptom fingerprint, logs NGINX, ConfigMap mount, remediation đã xác nhận và recovery criteria |

## Kết quả

| Iteration | Request | Memory | Kết quả |
|---|---|---|---|
| 1 | `01900000-0000-7000-8000-000000000403` | Không recall | AIC đọc live Deployment/Pods/Events/Service, xác định pods không Ready và Service không có backend; yêu cầu `describe` và `logs --previous`, chưa kết luận root cause. |
| 2 | `01900000-0000-7000-8000-000000000404` | Một memory đúng signature, score `0.7903664999999842` | AIC dùng log + ConfigMap hiện hành để xác định thiếu `;`, liên kết chính xác ConfigMap → NGINX exit 1 → CrashLoopBackOff → notReady endpoints → Service không phục vụ traffic. |

## Current evidence decisive ở iteration 2

- Pod: `CrashLoopBackOff`, exit code `1`, mount ConfigMap
  `edge-nginx-config` vào `/etc/nginx/conf.d/default.conf`.
- Log: `nginx: [emerg] unexpected "}" in /etc/nginx/conf.d/default.conf:6`.
- ConfigMap: `return 200 "edge gateway ready\\n"` thiếu dấu `;`.
- Endpoints: chỉ có `notReadyAddresses`, không có ready addresses.

## Đánh giá

Memory đã hoạt động đúng vai trò:

- Không xuất hiện ở iteration 1, khi chưa có incident signature.
- Ở iteration 2 chỉ recall resolution đã approved và signature khớp.
- AIC không dựa riêng historical case để kết luận: log và ConfigMap của incident
  hiện tại là provenance cho root cause.
- Memory giúp đề xuất đúng chuỗi kiểm tra: previous log → mount ConfigMap →
  content → endpoints/recovery.

Giới hạn của bài này: current log và ConfigMap đã chỉ rõ nguyên nhân, nên không
thể khẳng định score/độ chính xác tăng *do memory* chỉ với một run. Bài test này
đánh giá được retrieval, provenance và safety. Để đo hiệu quả, cần paired test
cùng fixture: một lần tắt recall, một lần bật recall, với evidence ban đầu chỉ
có CrashLoopBackOff và nhiều ConfigMap/sidecar/nguồn cấu hình khả dĩ.

## Sự cố vận hành quan sát được

Request `01900000-0000-7000-8000-000000000402` bị kẹt `processing` vì HolmesGPT
tool loop không có completion timeout. Container `holmesgpt` và `aic-api` đã
được restart; PostgreSQL, Qdrant và Kubernetes fixture được giữ nguyên. Đây là
một limitation cần xử lý trước khi demo tải dài.
