# HolmesGPT Iterative Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task.

**Goal:** Chạy lại các Run dưới 100 điểm bằng hội thoại điều tra lặp, trong đó HolmesGPT tự đề xuất bước kiểm tra/khắc phục và người thực thi chỉ gửi lại nhận định cùng output thực tế, không cung cấp oracle.

**Architecture:** Mỗi test có một phiên hội thoại độc lập cho Run A hoặc Run B. Vòng đầu gửi symptom; các vòng sau gửi nguyên văn câu trả lời trước đó kèm output lệnh do người thực thi chạy theo hướng dẫn. Hệ thống dừng khi HolmesGPT nêu đúng root cause có bằng chứng hoặc đạt giới hạn an toàn; toàn bộ transcript, command, output, iteration count và điểm được lưu trong thư mục test.

**Tech Stack:** HolmesGPT `/api/chat`, Kubernetes `kubectl`, Mem0 OSS/Qdrant local cho Run B, Markdown và JSON redacted.

**Spec:** User request 2026-08-18: iterative human-in-the-loop rerun; no answer injection; report chat history and iteration count.

## Global Constraints

- Run A không được seed hoặc chèn resolution/đáp án.
- Run B chỉ dùng memory của resolution đã được duyệt từ dữ liệu lịch sử, không chèn đáp án mới vào prompt điều tra.
- Sau mỗi HolmesGPT response, chỉ chạy các lệnh HolmesGPT yêu cầu; nếu lệnh có tác động, chỉ áp dụng trong namespace test và ghi nhận chính xác.
- Không tự diễn giải output thành đáp án trong message gửi HolmesGPT.
- Snapshot rollback point hiện có: `holmesgpt-batch-20260818` trên 5 VM.
- Dọn namespace test sau mỗi Run; xác minh node và HolmesGPT còn Ready/Running.

### Task 1: Iterative runner và transcript format

**Files:**
- Create: `scripts/holmes_eval/iterative_run.py`
- Create: `docs/testing/holmesgpt/iterative-rerun-protocol.md`

- [ ] Định nghĩa input gồm `case_id`, `run_id`, `namespace`, `initial_prompt`, `base_url`, `max_iterations`, và tùy chọn Mem0 retrieval.
- [ ] Mỗi vòng gọi HolmesGPT, parse response, trích xuất command/code block để người thực thi duyệt/chạy, nhưng không tự suy diễn root cause.
- [ ] Ghi JSON transcript với `iteration`, `holmes_message`, `executed_commands`, `command_outputs`, `operator_observation`, `timestamp`, `stop_reason`.
- [ ] RED: chạy fixture response có hai vòng và xác nhận transcript giữ nguyên message/output, không xuất hiện trường `oracle` hoặc `expected_answer` trong request.
- [ ] GREEN: triển khai runner hoặc workflow thủ công tương đương, test parser và redaction.
- [ ] REFACTOR: chuẩn hóa timeout, giới hạn lệnh nguy hiểm và giới hạn vòng lặp.

### Task 2: CKAD-LIFE-001 iterative rerun

**Files:**
- Create: `docs/testing/holmesgpt/CKAD-LIFE-001/run-a-r2-iterative.md`
- Create: `docs/testing/holmesgpt/CKAD-LIFE-001/run-b-r2-iterative.md`
- Modify: `docs/testing/holmesgpt/README.md`

- [ ] Dựng lại fault command/args làm container thoát.
- [ ] Run A: gửi symptom; chỉ chạy `kubectl` commands HolmesGPT yêu cầu; gửi output nguyên văn; lặp tới kết luận đúng hoặc giới hạn 5 vòng.
- [ ] Run B: cùng quy trình, có Mem0 retrieval nhưng không seed đáp án của fault hiện tại vào prompt.
- [ ] Ghi transcript, số vòng, thời gian, điểm và so sánh với Round 1.

### Task 3: CKAD-LIFE-002 iterative rerun

**Files:**
- Create: `docs/testing/holmesgpt/CKAD-LIFE-002/run-a-r2-iterative.md`
- Create: `docs/testing/holmesgpt/CKAD-LIFE-002/run-b-r2-iterative.md`
- Modify: `docs/testing/holmesgpt/README.md`

- [ ] Dựng lại invalid image tag.
- [ ] Chạy Run A và B theo cùng protocol, chú ý yêu cầu kiểm chứng DNS/registry thay vì mặc định một nguyên nhân.
- [ ] Ghi rõ vòng nào HolmesGPT sửa nhận định hoặc vẫn overclaim.

### Task 4: CKAD-SCHED-001 iterative rerun

**Files:**
- Create: `docs/testing/holmesgpt/CKAD-SCHED-001/run-a-r2-iterative.md`
- Modify: `docs/testing/holmesgpt/README.md`

- [ ] Dựng lại Pod request `cpu: "100"` vượt allocatable.
- [ ] Chỉ gửi output scheduler/node capacity theo lệnh HolmesGPT yêu cầu; không nói trước rằng `100` là 100 cores.
- [ ] Chấm khả năng HolmesGPT đọc đúng đơn vị CPU sau các vòng.

### Task 5: CKAD-CONF-002 iterative rerun

**Files:**
- Create: `docs/testing/holmesgpt/CKAD-CONF-002/run-a-r2-iterative.md`
- Modify: `docs/testing/holmesgpt/README.md`

- [ ] Dựng lại Secret tồn tại nhưng thiếu `MISSING_KEY`.
- [ ] Chạy iterative Run A; không cung cấp tên key thiếu ngoài symptom ban đầu nếu HolmesGPT chưa yêu cầu spec/events.
- [ ] Ghi lại mọi remediation đề xuất và kết quả xác minh.

### Task 6: CKAD-CONF-003 iterative rerun

**Files:**
- Create: `docs/testing/holmesgpt/CKAD-CONF-003/run-a-r2-iterative.md`
- Modify: `docs/testing/holmesgpt/README.md`

- [ ] Dựng lại `/missing/start` command.
- [ ] Chạy iterative Run A; chỉ thực thi lệnh HolmesGPT yêu cầu trong namespace test.
- [ ] Nếu HolmesGPT đề xuất patch, áp dụng đúng patch đó, gửi rollout/log output và ghi rõ số vòng đến khi recovery.

### Task 7: Review, verification và cleanup

- [ ] Kiểm tra mọi transcript không chứa API key, Secret value, hoặc oracle được chèn thủ công.
- [ ] Chạy `git diff --check`, kiểm tra YAML bằng `kubectl apply --dry-run=client` và xác minh namespace test đã xóa.
- [ ] Xác minh `kubectl get nodes` đều Ready và HolmesGPT deployment 1/1.
- [ ] Tổng hợp bảng Round 2: test | Run | số vòng | điểm cuối | thời gian | thay đổi nhận định | kết quả so với Round 1.
- [ ] Commit riêng Round 2 sau khi hoàn tất; không push nếu chưa có yêu cầu Git mới.
