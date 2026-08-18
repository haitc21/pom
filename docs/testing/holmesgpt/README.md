# HolmesGPT Evaluation Results

Bảng tổng hợp các bài test đánh giá độ chính xác và hiệu quả của HolmesGPT trong Kubernetes PoC.

| Tình huống | HolmesGPT | HolmesGPT + TencentDB | Đáp án |
|---|---|---|---|
| [CKAD-LIFE-001 — CrashLoopBackOff do command/args làm container thoát](CKAD-LIFE-001/) | [Đã chạy — 88/100](CKAD-LIFE-001/run-a-holmesgpt.md) | Chưa chạy | Container thoát với `exit 1` vì command/args cấu hình lỗi; cần khôi phục command chạy ứng dụng |

## Quy ước

- `run-a-holmesgpt.md`: lần chạy chỉ dùng HolmesGPT, không có bộ nhớ được truy hồi.
- `run-b-holmesgpt-memory.md`: lần chạy HolmesGPT có TencentDB Agent Memory.
- Điểm hiện tại là điểm provisional theo rubric trong [thiết kế đánh giá](../holmesgpt-memory-evaluation.md).
- Không ghi kết quả Run B trước khi thực sự chạy và chấm độc lập.

