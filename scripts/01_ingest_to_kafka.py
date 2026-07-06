# scripts/01_ingest_to_kafka.py
from kafka import KafkaProducer
import json, os, time

def ingest_data(records: list[dict]):
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    for record in records:
        producer.send("data.raw", key=record["id"].encode(), value=record).get(timeout=10)
        print(f"Sent: {record['id']}")
    producer.flush()

if __name__ == "__main__":
    sample_data = [
        {"id": "doc_001", "text": "AI platform integration test", "timestamp": time.time()},
        {"id": "doc_002", "text": "Kafka to Prefect pipeline", "timestamp": time.time()},
    ]
    ingest_data(sample_data)
    print("Integration 1 OK: Data → Kafka")
