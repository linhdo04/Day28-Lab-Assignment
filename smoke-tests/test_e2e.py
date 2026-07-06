import json
import time
import uuid
from pathlib import Path

import pandas as pd
import pytest
import redis
import requests
from kafka import KafkaProducer


BASE_URL = "http://localhost:8000"


def wait_until(predicate, timeout=30, interval=1):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(interval)
    pytest.fail(f"Condition was not met within {timeout}s")


class TestHappyPath:
    def test_full_inference_returns_answer(self):
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={"query": "What is platform engineering?", "embedding": [0.1] * 384},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        assert len(data["answer"]) > 10
        assert data["latency_ms"] < 15_000
        assert isinstance(data["degraded"], bool)

    def test_health_check_passes(self):
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDataIngestion:
    def test_kafka_record_reaches_delta(self):
        record_id = f"smoke_{uuid.uuid4().hex}"
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda value: json.dumps(value).encode(),
        )
        producer.send(
            "data.raw",
            key=record_id.encode(),
            value={"id": record_id, "text": "smoke test document", "timestamp": time.time()},
        ).get(timeout=10)
        producer.close()

        def record_in_delta():
            for path in Path("delta-lake/raw").glob("*.parquet"):
                if record_id in set(pd.read_parquet(path, columns=["id"])["id"]):
                    return True
            return False

        assert wait_until(record_in_delta)


class TestObservability:
    def test_prometheus_and_grafana_are_available(self):
        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": 'up{job="api-gateway"}'},
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()["data"]["result"]
        assert result and result[0]["value"][1] == "1"

        grafana = requests.get("http://localhost:3000/api/health", timeout=5)
        grafana.raise_for_status()


class TestFailurePath:
    def test_invalid_request_and_client_timeout_do_not_crash_gateway(self):
        invalid = requests.post(f"{BASE_URL}/api/v1/chat", json={}, timeout=5)
        assert invalid.status_code == 422

        with pytest.raises(requests.exceptions.Timeout):
            requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={"query": "timeout test", "embedding": [0.1] * 384},
                timeout=0.001,
            )

        wait_until(lambda: requests.get(f"{BASE_URL}/health", timeout=5).status_code == 200)


class TestFeatureStore:
    def test_feature_store_has_materialized_features(self):
        client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        assert client.ping()
        assert client.keys("feature:*")
