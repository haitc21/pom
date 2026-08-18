# CKAD-CONF-002 — Run A (HolmesGPT only)

## Fault và bằng chứng

- Namespace: `holmes-eval-ckad-conf-002-run-a`.
- Secret `app-secret` có key `EXISTING_KEY`, không có `MISSING_KEY`.
- Deployment `ckad-conf-002` dùng `secretKeyRef` tới `app-secret/MISSING_KEY`.
- Pod được schedule trên `k8s03`, image đã pull, nhưng container `nginx` ở `CreateContainerConfigError`.
- Event: `couldn't find key MISSING_KEY in Secret holmes-eval-ckad-conf-002-run-a/app-secret`.

## Kết quả HolmesGPT

HolmesGPT xác định đúng Secret key bị thiếu và đề xuất bổ sung key đã được phê duyệt hoặc cập nhật tham chiếu, sau đó kiểm tra rollout. Có một mô tả trạng thái Deployment không nhất quán (`Available` nhưng 0/1 Ready), nên trừ điểm chất lượng báo cáo.

**Điểm: 95/100.** Thời gian xử lý xấp xỉ 2m05s (từ request đến HTTP 200; không tính setup/cleanup).
