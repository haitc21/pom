# CKAD-CONF-003 — Run A (HolmesGPT only)

## Fault và bằng chứng

- Namespace: `holmes-eval-ckad-conf-003-run-a`.
- Image: `docker.io/library/nginx:1.27`; node: `k8s03`.
- Pod không Ready, container restart liên tục; termination `exitCode=127`.
- `command=/bin/sh -c`, `args=exec /missing/start`.
- Events: `Created`, `Started`, sau đó `Back-off restarting failed container`; log cho biết `/missing/start` không tồn tại.

## Kết quả HolmesGPT

HolmesGPT xác định chính xác command/args đã ghi đè entrypoint và gây exit 127. Khuyến nghị chính xác là xóa cả `command`/`args`; tuy nhiên một ví dụ thay args nhưng giữ shell command chưa đúng nên điểm remediation bị trừ nhẹ.

**Điểm: 95/100.** Thời gian xử lý xấp xỉ 2m05s (không tính setup/cleanup).
