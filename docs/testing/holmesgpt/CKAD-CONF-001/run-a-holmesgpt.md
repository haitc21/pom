# CKAD-CONF-001 — Run A (HolmesGPT only)

## Fault và bằng chứng

- Namespace: `holmes-eval-ckad-conf-001-run-a`
- Deployment: `ckad-conf-001`, image `nginx:1.27`, node `k8s03`.
- Pod ở `Pending`, container `Waiting/CreateContainerConfigError`.
- Event: `Error: configmap "missing-config" not found`.
- Image đã `Pulled`; Pod đã `Scheduled`, loại trừ lỗi image và scheduler.

## Kết quả HolmesGPT

HolmesGPT xác định đúng root cause là Deployment tham chiếu ConfigMap không tồn tại, đưa ra hai hướng xử lý an toàn (tạo/khôi phục ConfigMap hoặc bỏ tham chiếu nếu không cần), và nêu bước xác minh Pod/Deployment Ready. Không tự thực hiện remediation.

**Điểm: 100/100.** Thời gian xử lý xấp xỉ 2m05s (từ request đến HTTP 200; không tính setup/cleanup).
