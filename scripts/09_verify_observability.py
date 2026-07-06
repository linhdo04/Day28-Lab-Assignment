# scripts/09_verify_observability.py
import requests
from dotenv import load_dotenv

load_dotenv()

def check_prometheus():
    resp = requests.get(
        "http://localhost:9090/api/v1/query",
        params={"query": 'up{job="api-gateway"}'},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    assert data["status"] == "success"
    result = data["data"]["result"]
    assert result and result[0]["value"][1] == "1", "Prometheus is not scraping api-gateway"
    print("Integration 9 OK: Prometheus metrics flowing")

def check_langsmith():
    import os
    from langsmith import Client
    project = os.getenv("LANGCHAIN_PROJECT", "lab28-platform")
    client = Client(api_key=os.environ["LANGCHAIN_API_KEY"])
    runs = list(client.list_runs(project_name=project, limit=1))
    assert len(runs) > 0
    print(f"Integration 10 OK: LangSmith traces visible in {project}")

if __name__ == "__main__":
    check_prometheus()
    check_langsmith()
