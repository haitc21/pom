# CKAD-SCHED-001 — Pod Pending do CPU request vượt allocatable

| Lần chạy | Phạm vi | Trạng thái | Điểm | Thời gian |
|---|---|---|---:|---:|
| [Run A](run-a-holmesgpt.md) | HolmesGPT only | Hoàn tất | 70/100 | ~1m22s |
| [Run B](run-b-holmesgpt-memory.md) | HolmesGPT + POM Memory (Mem0 OSS) | Hoàn tất | 100/100 | ~1m08s |

Oracle: request `cpu: "100"` nghĩa là 100 cores, vượt allocatable 2 cores trên mỗi node. Scheduler báo `Insufficient cpu`; k8s01 còn có control-plane taint. Run A đọc sai quantity thành 100m; Run B dùng memory đã duyệt và sửa được lỗi semantic.

Paired delta: **+30 điểm**. Đây là bằng chứng rõ ràng memory giúp giảm lỗi hiểu sai đơn vị resource, nhưng cần kiểm tra thêm các quantity khác.
