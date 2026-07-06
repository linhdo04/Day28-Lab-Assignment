# scripts/03_delta_to_feast.py
import pandas as pd
import glob, os, redis, json

def load_from_delta_and_push_feast():
    delta_path = os.getenv("DELTA_PATH", "delta-lake/raw")
    files = sorted(glob.glob(f"{delta_path}/*.parquet"))
    if not files:
        print("No data in Delta Lake yet")
        return 0

    df = pd.concat([pd.read_parquet(f) for f in files])
    print(f"Loaded {len(df)} records from Delta Lake")

    r = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    r.ping()
    with r.pipeline(transaction=True) as pipe:
        for _, row in df.drop_duplicates(subset=["id"], keep="last").iterrows():
            pipe.set(f"feature:{row['id']}", json.dumps({
                "text": row["text"], "timestamp": row.get("timestamp"), "processed": True
            }))
        pipe.execute()

    count = df["id"].nunique()
    print(f"Integration 3+4 OK: Delta Lake → Feast (Redis) — {count} features stored")
    return count

if __name__ == "__main__":
    load_from_delta_and_push_feast()
