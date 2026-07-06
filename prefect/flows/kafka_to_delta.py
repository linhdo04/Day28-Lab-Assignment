# prefect/flows/kafka_to_delta.py
from prefect import flow, task
from kafka import KafkaConsumer
import json, os, time
import pandas as pd
from datetime import datetime

@task
def consume_and_process():
    """Consume data from Kafka topic"""
    consumer = KafkaConsumer(
        "data.raw",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
        group_id="lab28-kafka-to-delta",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
        value_deserializer=lambda m: json.loads(m.decode())
    )
    records = []
    for msg in consumer:
        records.append(msg.value)

    print(f"Consumed {len(records)} records from Kafka")
    consumer.close()
    return records

@task
def save_to_delta(records):
    """Save records to Delta Lake (parquet format)"""
    if not records:
        print("No records to save")
        return None
    
    df = pd.DataFrame(records)
    # Giả lập Delta Lake bằng parquet (local volume)
    path = "/opt/delta-lake/raw"
    os.makedirs(path, exist_ok=True)
    output = f"{path}/batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.parquet"
    df.to_parquet(output, index=False)
    print(f"Saved {len(df)} records to Delta Lake")
    return output

@flow(name="Kafka to Delta Pipeline", log_prints=True)
def kafka_to_delta_flow():
    """Main flow: consume from Kafka and save to Delta Lake"""
    records = consume_and_process()
    save_to_delta(records)

if __name__ == "__main__":
    interval = int(os.getenv("PIPELINE_INTERVAL_SECONDS", "15"))
    # Prefect 2 retains state between repeated in-process runs. Exit periodically so
    # Docker can recreate a clean process instead of allowing unbounded memory growth.
    max_runs = int(os.getenv("MAX_FLOW_RUNS_PER_PROCESS", "20"))
    for _ in range(max_runs):
        kafka_to_delta_flow()
        time.sleep(interval)
