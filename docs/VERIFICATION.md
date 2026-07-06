# Verification Results

Ngày kiểm tra: 2026-07-06 (Asia/Ho_Chi_Minh)

- Docker Compose: 9/9 services running; Kafka healthy.
- Smoke tests: 6/6 passed, covering 5 required end-to-end journeys.
- Production readiness: 13/13 checks passed, score 100%, status READY.
- Kafka → Prefect → Delta: verified with a unique smoke-test record.
- Redis feature store: populated.
- Qdrant collection `documents`: populated.
- Prometheus target `api-gateway`: `up=1`.
- Grafana dashboard `lab28-platform`: provisioned.
- Prometheus alerts `ApiGatewayDown` and `ApiGatewayHighErrorRate`: loaded and healthy.

External limitations at verification time:

- The configured vLLM ngrok endpoint was unavailable. Gateway graceful degradation was
  verified and returns `degraded=true` with a fallback response.
- LangSmith rejected trace ingestion with HTTP 403. Replace the API key before capturing
  the final LangSmith screenshot.
