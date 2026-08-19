# CKAD-LIFE-002-AIC — thử lại chính sách memory theo bằng chứng

Ngày chạy: 2026-08-19  
Conversation mới: `b13d6b1a-1ad3-4611-8d2c-0296f20dc521`

## Mục tiêu

Kiểm tra memory chỉ gợi ý hướng điều tra, không được dùng kết quả của sự cố cũ
như bằng chứng cho sự cố hiện tại. Fixture được dựng lại trong namespace
`holmes-eval-ckad-life-002-aic` trước khi tạo conversation mới.

## Chính sách áp dụng

- Không recall memory ở iteration 1.
- Chỉ recall sau khi command output hiện tại tạo được incident signature.
- Chỉ nhận resolution đã approved, đúng signature và score tối thiểu `0.45`.
- Prompt phân tách `CURRENT_EVIDENCE` và historical guidance.

Resolution guidance được dùng trong lượt này:

- Resolution: `ckad-life-002-image-pull-guidance-v2`
- Memory: `69169d9a-f5e2-4bb5-9423-17bb1a6bc469`
- Signature: `image_pull_failure / ImagePullBackOff / Pod`

## Kết quả từng iteration

| Iteration | Request ID | Memory | Bằng chứng cung cấp | Kết quả chính |
|---|---|---|---|---|
| 1 | `01900000-0000-7000-8000-000000000201` | Không, `memory_references=[]` | Chỉ mô tả triệu chứng; HolmesGPT tự đọc Kubernetes | Nhận diện `ImagePullBackOff` và DNS error, nhưng không lấy historical `404` làm bằng chứng. Image không tồn tại chỉ được giữ ở mức giả thuyết. |
| 2 | `01900000-0000-7000-8000-000000000202` | Guidance v2, score `0.764565` | Registry không auth trả `401`; DNS trên k8s03 trả `REFUSED`; pod hiện tại `ImagePullBackOff` kèm DNS error | Phân biệt đúng `401` chưa chứng minh image tồn tại hay không; xác nhận DNS hiện hành; bác bỏ historical `404` như bằng chứng và yêu cầu authenticated lookup. |
| 3 | `01900000-0000-7000-8000-000000000203` | Guidance v2, score `0.801235` | Authenticated lookup hiện tại trả `404 MANIFEST_UNKNOWN`; DNS `REFUSED`; pod hiện tại `ImagePullBackOff` | Kết luận image tag không tồn tại dựa trên current 404; tách DNS node là lỗi hạ tầng độc lập; nêu provenance cho cả hai. |

## So sánh với hành vi cũ

Trước thay đổi, lượt đầu có memory đã lấy cả resolution tương đồng và memory
CrashLoopBackOff không phù hợp. HolmesGPT dùng kết quả `404 MANIFEST_UNKNOWN` của
sự cố lịch sử như thể đã được quan sát trong incident mới, dẫn tới kết luận sớm
và sai provenance.

Sau thay đổi:

- Iteration 1 không bị anchoring bởi memory.
- Iteration 2 chỉ nhận đúng một guidance có signature khớp.
- Guidance đã giúp chọn phép kiểm tra quyết định nhưng không thay phép kiểm tra đó.
- Kết luận cuối chỉ xuất hiện sau khi current authenticated lookup trả `404`.

## Đánh giá

Mục tiêu evidence firewall đạt: memory cải thiện đường điều tra mà không đóng vai
trò đáp án. Với bài test này, cần ba iteration để đạt kết luận có bằng chứng rõ
ràng thay vì kết luận ngay bằng dữ liệu lịch sử.

Các hạn chế còn lại:

- HolmesGPT vẫn đôi lúc gọi một tag có vẻ bất thường là “không hợp lệ” trước khi
  registry xác nhận; đây chỉ nên là heuristic.
- Một số lệnh gợi ý dùng `kubectl debug`, thực chất tạo resource và không phải
  read-only. AIC không tự chạy chúng, nhưng cần thêm command safety classifier.
- Lệnh đọc kubelet bằng label `k8s-app=kubelet` có thể không hợp lệ trên kubeadm;
  nên ưu tiên SSH/journalctl read-only hoặc một collector được kiểm soát.
- Kết luận “nguyên nhân trực tiếp” cần hiểu là cấu hình image chắc chắn sai; DNS
  cũng là blocker thực tế của lần pull hiện tại, vì vậy cả hai đều phải được xử lý
  trước khi xác minh workload phục hồi.
