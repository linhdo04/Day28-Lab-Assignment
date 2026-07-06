# api-gateway/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

try:
    from langsmith import traceable
except ImportError:
    def traceable(*_args, **_kwargs):
        return lambda fn: fn

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"].rstrip("/")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "5"))


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    embedding: list[float] = Field(min_length=1)

@app.post("/api/v1/chat")
@traceable(name="api-gateway-chat", run_type="chain")
async def chat(body: ChatRequest):
    start = time.time()
    context = []
    degraded_reasons = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            search_resp = await client.post(
                f"{QDRANT_URL}/collections/documents/points/search",
                json={"vector": body.embedding, "limit": 3, "with_payload": True},
            )
            search_resp.raise_for_status()
            context = search_resp.json().get("result", [])
    except httpx.HTTPError:
        degraded_reasons.append("vector_store_unavailable")

    try:
        prompt = f"Context: {context}\n\nQuery: {body.query}"
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
            })
            llm_resp.raise_for_status()
    except httpx.TimeoutException as exc:
        degraded_reasons.append("llm_timeout")
        result = None
    except httpx.HTTPError:
        degraded_reasons.append("llm_unavailable")
        result = None
    else:
        result = llm_resp.json()

    latency = (time.time() - start) * 1000
    if result is None:
        answer = (
            "The model service is temporarily unavailable. "
            "Your request was accepted and the platform is running in degraded mode."
        )
    else:
        answer = result["choices"][0]["message"]["content"]

    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": result.get("model", MODEL) if result else MODEL,
        "degraded": bool(degraded_reasons),
        "degraded_reasons": degraded_reasons,
    }

@app.get("/health")
def health():
    return {"status": "ok"}
