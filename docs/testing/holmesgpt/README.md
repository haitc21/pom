# HolmesGPT Evaluation Results

Bảng tổng hợp các bài test đánh giá độ chính xác và hiệu quả của HolmesGPT trong Kubernetes PoC.

| Tình huống | HolmesGPT | HolmesGPT + POM Memory | Đáp án |
|---|---|---|---|
| [CKAD-LIFE-001 — CrashLoopBackOff do command/args làm container thoát](CKAD-LIFE-001/) | [Đã chạy — 88/100](CKAD-LIFE-001/run-a-holmesgpt.md) | [Đã chạy — 100/100](CKAD-LIFE-001/run-b-holmesgpt-memory.md) | Container thoát với `exit 1` vì command/args cấu hình lỗi; cần khôi phục command chạy ứng dụng |

## Quy ước

- `run-a-holmesgpt.md`: lần chạy chỉ dùng HolmesGPT, không có bộ nhớ được truy hồi.
- `run-b-holmesgpt-memory.md`: lần chạy HolmesGPT có POM Memory triển khai bằng Mem0 OSS và resolution đã duyệt.
- Điểm hiện tại là điểm provisional theo rubric trong [thiết kế đánh giá](../holmesgpt-memory-evaluation.md).
- Run B đã được chạy và chấm độc lập; các cohort paraphrase, analogous và hard-negative vẫn chưa chạy.
