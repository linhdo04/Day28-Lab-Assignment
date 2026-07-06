# Milestone 3 Demo Runbook

## Trước khi demo

```bash
docker compose up -d --build
python scripts/01_ingest_to_kafka.py
sleep 20
python scripts/03_delta_to_feast.py
python scripts/05_embed_to_qdrant.py
pytest smoke-tests -v
python scripts/production_readiness_check.py
```

Xác nhận các trang: Prefect `:4200`, Grafana `:3000/d/lab28-platform`, Prometheus
`:9090`, Qdrant `:6333/dashboard` và API docs `:8000/docs`.

## Kịch bản 15 phút

1. **Kiến trúc (2 phút):** trình bày luồng Kafka → Prefect → Delta → Redis/Qdrant và
   ranh giới mạng tới GPU Kaggle.
2. **Happy path (5 phút):** chạy producer, xem flow run trong Prefect, gọi
   `POST /api/v1/chat`, rồi kiểm tra vector và feature count.
3. **Failure path (3 phút):** tạm dừng Qdrant, gọi lại API và chỉ ra
   `degraded=true`; khởi động lại Qdrant ngay sau đó.
4. **Observability (3 phút):** tạo request traffic, mở dashboard để xem request rate,
   P95 latency và 5xx rate; mở trang Prometheus alerts.
5. **Q&A (2 phút):** dùng các quyết định và trade-off trong `SUBMISSION_ANSWERS.md`.

## Lệnh demo an toàn

```bash
python -c 'import requests; print(requests.post(
  "http://localhost:8000/api/v1/chat",
  json={"query":"Explain event-driven AI platforms","embedding":[0.1]*384},
  timeout=15).json())'

docker compose stop qdrant
# gọi lại request trên: gateway vẫn trả answer fallback và degraded=true
docker compose start qdrant
```

Không dừng Kafka trong lúc demo ingestion vì sẽ làm flow chờ broker. Không trình bày
LangSmith là hoạt động nếu API key đang trả 403; thay key và chạy
`scripts/09_verify_observability.py` trước buổi demo.
