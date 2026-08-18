# CKAD-LIFE-002 — Run A Round 2 (điều tra lặp)

## Kết quả

- **Điểm cuối:** 85/100 (chưa đạt 100; không thể xác nhận image tag độc lập do môi trường không có DNS/egress tới Docker Hub).
- **Số vòng HolmesGPT:** 4 lượt.
- **Namespace:** `holmes-eval-ckad-life-002-r2-a`.

## Lịch sử chat và hành động

1. **Vòng 1:** gửi symptom-only. HolmesGPT xác định `ImagePullBackOff`, nhưng còn giữ hai giả thuyết image tag không tồn tại và DNS/network; yêu cầu debug DNS, kiểm tra Deployment và thử image `nginx:latest`.
2. **Vòng 2:** kỹ sư thực thi đúng các lệnh. Output xác nhận lỗi DNS `lookup registry-1.docker.io ... server misbehaving`; thử `nginx:latest` cũng `ImagePullBackOff`. HolmesGPT vẫn chưa thể phân biệt tag sai với hạ tầng.
3. **Vòng 3:** kỹ sư thực thi debug DNS trên node và `kubectl get networkpolicy -A`; các debug pod `busybox` cũng không pull được do cùng lỗi registry/DNS. Output được gửi nguyên văn; không bổ sung đáp án.
4. **Vòng 4:** HolmesGPT kết luận chắc chắn lỗi DNS/network trên node, nhưng vẫn suy diễn `busybox:latest` tồn tại dù chưa có bằng chứng registry. Đây là overclaim; image tag `nginx:99.99.99-postops-invalid` chưa được chứng minh độc lập là nguyên nhân duy nhất.

## Đánh giá

Iterative workflow làm rõ lỗi hạ tầng và ngăn kết luận quá sớm rằng tag chắc chắn sai, nhưng HolmesGPT vẫn overclaim về image tồn tại. Điểm provisional: **85/100**; cần bổ sung kiểm thử registry có kiểm soát hoặc mirror/cache nội bộ để chấm dứt ambiguity.
