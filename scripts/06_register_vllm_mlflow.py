"""Register the externally served vLLM endpoint in MLflow.

Run this where MLflow credentials and VLLM_NGROK_URL are available.
"""

import os

import mlflow
import requests
from dotenv import load_dotenv

load_dotenv()


def register_serving_endpoint() -> str:
    vllm_url = os.environ["VLLM_NGROK_URL"].rstrip("/")
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    model_name = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4")

    health = requests.get(f"{vllm_url}/health", timeout=15)
    health.raise_for_status()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("lab28-integration")

    with mlflow.start_run(run_name="vllm-serving-v1") as run:
        mlflow.log_params({"model": model_name, "serving_engine": "vLLM"})
        mlflow.set_tags({
            "serving_url": vllm_url,
            "deployment_status": "production",
            "registry_alias": "champion",
        })
        run_id = run.info.run_id

    print(f"Integration 6+7 OK: MLflow run {run_id} → vLLM endpoint")
    return run_id


if __name__ == "__main__":
    register_serving_endpoint()
