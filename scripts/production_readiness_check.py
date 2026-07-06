"""Automated local production-readiness assessment."""

from pathlib import Path

import redis
import requests
from kafka.admin import KafkaAdminClient


results = {}


def check(name, fn):
    try:
        fn()
        results[name] = "PASS"
        print(f"  [PASS] {name}")
    except Exception as exc:
        results[name] = f"FAIL: {exc}"
        print(f"  [FAIL] {name}: {exc}")


def get(url, **kwargs):
    response = requests.get(url, timeout=5, **kwargs)
    response.raise_for_status()
    return response


def assert_prometheus_target_up():
    data = get(
        "http://localhost:9090/api/v1/query",
        params={"query": 'up{job="api-gateway"}'},
    ).json()
    assert data["data"]["result"], "api-gateway target is missing"
    assert data["data"]["result"][0]["value"][1] == "1"


def assert_collection_has_points():
    data = get("http://localhost:6333/collections/documents").json()
    assert data["result"]["points_count"] > 0


def assert_features_exist():
    client = redis.Redis(host="localhost", port=6379, socket_timeout=5)
    assert client.ping()
    assert client.keys("feature:*")


def assert_kafka_topic_exists():
    admin = KafkaAdminClient(bootstrap_servers="localhost:9092", request_timeout_ms=5000)
    try:
        assert "data.raw" in admin.list_topics()
    finally:
        admin.close()


def assert_delta_data_exists():
    assert list(Path("delta-lake/raw").glob("*.parquet"))


def main():
    print("\n=== RELIABILITY ===")
    check("Health endpoint", lambda: get("http://localhost:8000/health"))
    check("OpenAPI docs", lambda: get("http://localhost:8000/docs"))
    check("Prefect API", lambda: get("http://localhost:4200/api/health"))

    print("\n=== OBSERVABILITY ===")
    check("Prometheus healthy", lambda: get("http://localhost:9090/-/healthy"))
    check("Grafana healthy", lambda: get("http://localhost:3000/api/health"))
    check("Gateway metrics exposed", lambda: get("http://localhost:8000/metrics"))
    check("Prometheus target up", assert_prometheus_target_up)

    print("\n=== SECURITY ===")
    check(
        "Unknown admin route rejected",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected route"))
        if requests.get("http://localhost:8000/admin", timeout=5).status_code != 404
        else None,
    )

    print("\n=== DATA SERVICES ===")
    check("Qdrant healthy", lambda: get("http://localhost:6333/healthz"))
    check("Qdrant collection populated", assert_collection_has_points)
    check("Redis features populated", assert_features_exist)
    check("Kafka topic exists", assert_kafka_topic_exists)
    check("Delta data exists", assert_delta_data_exists)

    passed = sum(value == "PASS" for value in results.values())
    total = len(results)
    score = passed / total * 100
    print("\n" + "=" * 44)
    print(f"Production Readiness Score: {passed}/{total} = {score:.0f}%")
    print(f"Target: >80% — Status: {'READY' if score > 80 else 'NOT READY'}")
    return 0 if score > 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
