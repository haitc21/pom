# CKAD-LIFE-001 — Run A Round 2 (điều tra lặp)

## Kết quả

- **Điểm cuối:** 100/100
- **Số vòng HolmesGPT:** 4 lượt (3 lượt điều tra + 1 lượt xác nhận)
- **Kết quả phục hồi:** Deployment `1/1`, Pod `1/1 Running`, restart count `0`.
- **Namespace:** `holmes-eval-ckad-life-001-r2-a`

## Lịch sử chat và hành động

### Vòng 1 — symptom-only

**Gửi HolmesGPT:** Deployment không có Pod khả dụng; yêu cầu bắt đầu điều tra bằng Kubernetes/Prometheus, nếu cần thì đưa lệnh kiểm tra, chưa kết luận khi thiếu bằng chứng.

**HolmesGPT:** kiểm tra trực tiếp và xác định sơ bộ Pod `Running` nhưng container `Error`, exit code `1`, command in lỗi rồi thoát; yêu cầu chạy `kubectl logs --previous`, `kubectl describe pod` và `kubectl get deployment -o yaml`.

**Kỹ sư thực thi, không bổ sung nhận định:**

- `kubectl logs --previous`: runtime không còn log previous (`unable to retrieve container logs`), không tự suy diễn.
- `kubectl describe pod`: command `/bin/sh -c`, args `echo fatal: configuration file /etc/demo/app.yaml not found >&2; exit 1`, `State=Terminated`, `Exit Code=1`, `BackOff`, `Ready=False`.
- `kubectl get deployment -o yaml`: xác nhận cùng command/args và `availableReplicas` không có.

### Vòng 2 — gửi output nguyên văn

**Gửi HolmesGPT:** chỉ bao quanh output ba lệnh trên bằng `BEGIN/END COMMAND OUTPUT`, yêu cầu cập nhật điều tra và chỉ đưa lệnh tiếp theo nếu cần.

**HolmesGPT:** xác nhận command/args bị ghi đè và đề xuất lệnh `kubectl set image` (đồng thời cảnh báo lệnh này không xóa command/args), sau đó hướng dẫn xóa command/args.

**Kỹ sư thực thi đúng lệnh HolmesGPT yêu cầu:** `kubectl set image ... nginx:1.27 --record`; rollout timeout, Pod vẫn `CrashLoopBackOff`, JSONPath xác nhận command/args vẫn còn.

### Vòng 3 — gửi output remediation thất bại

**Gửi HolmesGPT:** chỉ gửi output rollout timeout, Pod vẫn `CrashLoopBackOff`, command/args vẫn tồn tại.

**HolmesGPT:** cập nhật hướng dẫn: xóa hai trường `command` và `args` bằng `kubectl edit`/patch; không cung cấp thêm kết luận ngoài bằng chứng hiện tại.

**Kỹ sư thực thi tương đương patch JSON:** remove `/spec/template/spec/containers/0/command` và `/args`; rollout thành công, Pod mới `1/1 Running`, restart `0`.

### Vòng 4 — xác nhận

**Gửi HolmesGPT:** output patch và xác minh rollout thành công nguyên văn.

**HolmesGPT:** xác nhận sự cố đã phục hồi, root cause là command/args ghi đè entrypoint khiến process thoát code `1`, và không cần thay đổi thêm.

## Đánh giá

Round 1 đạt 88/100 do mô tả phase không khớp snapshot. Round 2 đạt 100/100 nhờ kiểm tra theo thời gian thực, thực thi remediation theo hướng dẫn và gửi lại kết quả thực tế qua 3 vòng.
