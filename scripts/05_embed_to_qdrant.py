# scripts/05_embed_to_qdrant.py
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os, uuid

load_dotenv()
EMBED_URL = os.environ["EMBED_NGROK_URL"].rstrip("/")
COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

def embed_and_store(records: list[dict]):
    if not records:
        return 0
    response = requests.post(
        f"{EMBED_URL}/embed",
        json={"texts": [r["text"] for r in records]},
        timeout=30,
    )
    response.raise_for_status()
    embeddings = response.json()["embeddings"]
    if len(embeddings) != len(records) or not embeddings:
        raise ValueError("Embedding service returned an invalid number of vectors")

    vector_size = len(embeddings[0])
    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, str(rec["id"]))),
            vector=emb,
            payload=rec,
        )
        for emb, rec in zip(embeddings, records)
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points, wait=True)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")
    return len(points)

# Test với sample data
if __name__ == "__main__":
    embed_and_store([
        {"id": "doc_001", "text": "AI platform integration test"},
        {"id": "doc_002", "text": "Kafka to Prefect pipeline"},
    ])
