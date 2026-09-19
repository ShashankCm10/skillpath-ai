import asyncio

import httpx

from app.main import app


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def test_analysis_workflow_persists_logs_and_assistant_response():
    response = request("POST", "/api/analyze", json={"profile": {"skills": ["Fastapi"]}})
    assert response.status_code == 200
    analysis = response.json()
    assert analysis["target_job"]
    assert len(analysis["logs"]) >= 5

    logs = request("GET", f"/api/agent-logs/{analysis['id']}")
    assert logs.status_code == 200
    assert len(logs.json()["logs"]) == len(analysis["logs"])

    assistant = request(
        "POST",
        "/api/assistant",
        json={"message": "What should I focus on?", "analysis_id": analysis["id"]},
    )
    assert assistant.status_code == 200
    assert assistant.json()["reply"]


def test_missing_analysis_is_a_404():
    assert request("GET", "/api/analysis/missing").status_code == 404
    assert request("GET", "/api/agent-logs/missing").status_code == 404
    assert request("GET", "/api/roadmap/missing").status_code == 404