import asyncio

import httpx

from app.engine import parse_profile
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


def test_jobs_endpoint_uses_the_supplied_profile():
    electrical = request(
        "GET",
        "/api/jobs",
        params=[
            ("skills", "Circuit Analysis"),
            ("skills", "MATLAB"),
            ("skills", "AutoCAD"),
            ("skills", "Power Systems"),
            ("interests", "Electrical Engineering"),
            ("interests", "Electronics"),
            ("target_role", "Electrical Engineer"),
            ("location", "Bengaluru"),
        ],
    )
    software = request(
        "GET",
        "/api/jobs",
        params=[
            ("skills", "Python"),
            ("skills", "React"),
            ("skills", "FastAPI"),
            ("skills", "SQL"),
            ("interests", "Software Engineering"),
            ("interests", "Web Development"),
            ("target_role", "Full Stack Developer"),
            ("location", "Bengaluru"),
        ],
    )

    assert electrical.status_code == 200
    assert software.status_code == 200
    assert electrical.json()["jobs"][0]["domain"] in {"Electrical", "Electronics"}
    assert software.json()["jobs"][0]["domain"] == "Software/IT"
    assert electrical.json()["jobs"][0]["id"] != software.json()["jobs"][0]["id"]


def test_analyze_preserves_current_skill_payload_without_defaults():
    response = request(
        "POST",
        "/api/analyze",
        json={
            "profile": {
                "education": "B.E. Electronics and Communication Engineering",
                "skills": ["VLSI & Digital Design", "MATLAB"],
                "location": "Bengaluru",
                "interests": ["Electronics Engineer"],
                "target_role": "Electronics Engineer",
            }
        },
    )

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["skills"] == ["Vlsi & Digital Design", "Matlab"]
    assert "Python" not in profile["skills"]
    assert "JavaScript" not in profile["skills"]
    assert response.json()["target_job"]["domain"] in {"Electronics", "Electrical"}


def test_analyze_uses_current_profile_target():
    profiles = [
        {
            "education": "B.E. Electronics and Communication Engineering",
            "skills": ["VLSI & Digital Design"],
            "location": "Bengaluru",
            "interests": ["Electronics Engineer"],
            "target_role": "Electronics Engineer",
            "experience": "Student / Fresher",
        },
        {
            "skills": ["Python", "React", "FastAPI", "SQL"],
            "interests": ["Software Engineering"],
            "target_role": "Full Stack Developer",
        },
        {
            "skills": ["Financial Analysis", "Excel", "Accounting"],
            "interests": ["Finance", "MBA"],
            "target_role": "Financial Analyst",
        },
    ]
    results = [request("POST", "/api/analyze", json={"profile": profile}).json() for profile in profiles]

    assert results[0]["target_job"]["domain"] == "Electronics"
    assert results[1]["target_job"]["domain"] == "Software/IT"
    assert results[2]["target_job"]["domain"] in {"Finance", "Accounting", "MBA/Management"}
    assert len({result["target_job"]["id"] for result in results}) == 3


def test_parse_profile_keeps_multispace_domain_terms():
    profile = parse_profile({
        "skills": ["Power Systems", "Financial Analysis", "MBA", "Electrical Engineering"],
        "interests": ["Electrical Engineering", "MBA"],
        "target_role": "Power Systems Engineer",
    })

    assert "Power Systems" in profile["skills"]
    assert "Financial Analysis" in profile["skills"]
    assert "MBA" in profile["skills"]
    assert "Electrical Engineering" in profile["skills"]