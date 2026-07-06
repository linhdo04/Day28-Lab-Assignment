# Câu trả lời nộp bài

## 1. Trade-off kiến trúc

Kafka và Prefect thêm độ phức tạp vận hành nhưng tách producer khỏi xử lý batch, cho
phép replay và retry. Delta dạng Parquet đơn giản, dễ kiểm tra nhưng chưa có transaction
log như Delta Lake thật. Redis tối ưu truy cập feature online; Qdrant phục vụ semantic
search. Gateway tập trung timeout, validation, fallback và telemetry để các client không
phải hiểu từng backend.

## 2. Ngắt kết nối Local–Kaggle

Gateway đặt timeout cho vLLM và trả response degraded có cấu trúc khi tunnel lỗi. Qdrant
cũng được cô lập: lỗi vector search không làm gateway crash. Đây là fallback tĩnh, phù hợp
demo; production nên thêm circuit breaker, retry có jitter và cache câu trả lời đã duyệt.

## 3. Kafka và decoupling

Producer chỉ biết topic `data.raw`, không biết Prefect, Parquet hoặc feature store. Consumer
dùng group id và offset để xử lý độc lập, có thể dừng rồi tiếp tục. Thành phần downstream
có thể scale hoặc được thay thế mà không đổi producer, đồng thời event cũ có thể replay.

## 4. Observability

FastAPI xuất Prometheus metrics. Prometheus scrape gateway và đánh giá alert rules;
Grafana được provision sẵn dashboard request rate, P95 latency và 5xx rate. Prefect lưu
flow/task logs và trạng thái run. Gateway dùng LangSmith `traceable` cho inference chain;
trace cloud phụ thuộc API key hợp lệ.

## 5. Service crash

Compose restart/health dependency bảo đảm Kafka chỉ mở worker sau khi broker healthy.
Consumer giữ offset nên có thể tiếp tục sau restart. Gateway trả degraded response khi
Qdrant/vLLM lỗi thay vì phát sinh unhandled exception. Redis và Qdrant dùng persistent
volume. Production cần bổ sung replicated brokers/stores, backup, alert routing và runbook
rollback; cấu hình lab hiện vẫn là single-node.
