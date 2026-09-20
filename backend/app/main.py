from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .data import COURSES, DEFAULT_PROFILE, JOBS
from .engine import Workflow, match_jobs, parse_profile
from .llm import assistant_reply
from .db import get_analysis, save_analysis

app = FastAPI(title="SkillPath AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517[0-9]+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ANALYSES: dict[str, dict[str, Any]] = {}
PROFILE: dict[str, Any] = DEFAULT_PROFILE.copy()
try:
    from .db import init_db
    init_db()
except Exception:
    pass

class ProfileIn(BaseModel):
    name: str = "Demo User"; education: str = ""; skills: list[str] = Field(default_factory=list); location: str = ""; interests: list[str] = Field(default_factory=list); target_role: str = ""; experience: str = ""; resume_text: str = ""
class AnalyzeIn(BaseModel):
    profile: ProfileIn | None = None; job_id: str | None = None; free_only: bool = False
class AssistantIn(BaseModel):
    message: str
    profile: ProfileIn | None = None
    analysis_id: str | None = None

@app.get("/api/health")
def health(): return {"status": "ok", "service": "skillpath-ai", "ai_mode": "deterministic fallback", "jobs": len(JOBS), "courses": len(COURSES)}

@app.post("/api/profile")
def save_profile(payload: ProfileIn):
    global PROFILE
    PROFILE = parse_profile(payload.model_dump())
    return PROFILE

@app.post("/api/profile/resume")
async def upload_resume(file: UploadFile = File(...)):
    data = await file.read()
    text = data.decode("utf-8", errors="ignore")
    if file.filename and file.filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            raise HTTPException(status_code=422, detail="Unable to read PDF resume")
    elif file.filename and file.filename.lower().endswith(".docx"):
        try:
            from docx import Document
            import io
            text = "\n".join(paragraph.text for paragraph in Document(io.BytesIO(data)).paragraphs)
        except Exception:
            raise HTTPException(status_code=422, detail="Unable to read DOCX resume")
    return {"filename": file.filename, "text": text[:20000], "profile": parse_profile({**PROFILE, "resume_text": text}, text)}

@app.get("/api/jobs")
def jobs(
    q: str = "",
    location: str = "",
    work_mode: str = "",
    skills: list[str] = Query(default=[]),
    interests: list[str] = Query(default=[]),
    education: str = "",
    target_role: str = "",
    experience: str = "",
    resume_text: str = "",
):
    has_profile = bool(skills or interests or education or target_role or experience or resume_text)
    items = match_jobs({
        "skills": skills,
        "interests": interests,
        "education": education,
        "target_role": target_role,
        "experience": experience,
        "resume_text": resume_text,
    }) if has_profile else JOBS
    if q: items = [j for j in items if q.lower() in json.dumps(j).lower()]
    if location: items = [j for j in items if location.lower() in j["location"].lower()]
    if work_mode: items = [j for j in items if work_mode.lower() == j["work_mode"].lower()]
    return {"jobs": items, "count": len(items)}

@app.post("/api/analyze")
def analyze(payload: AnalyzeIn):
    workflow = Workflow(); result = workflow.run(parse_profile((payload.profile or ProfileIn(**PROFILE)).model_dump()), payload.job_id, payload.free_only)
    ANALYSES[result["id"]] = result
    save_analysis(result)
    return result

@app.get("/api/analysis/{analysis_id}")
def analysis(analysis_id: str):
    result = ANALYSES.get(analysis_id) or get_analysis(analysis_id)
    if not result: raise HTTPException(status_code=404, detail="Analysis not found")
    return result

@app.get("/api/courses")
def courses(free_only: bool = False): return {"courses": [c for c in COURSES if not free_only or c["is_free"]], "count": len(COURSES)}

@app.get("/api/roadmap/{analysis_id}")
def roadmap(analysis_id: str, free_only: bool = False):
    result = ANALYSES.get(analysis_id) or get_analysis(analysis_id)
    if not result: raise HTTPException(status_code=404, detail="Analysis not found")
    from .engine import build_gap
    gap = build_gap(result["target_job"], result["profile"], free_only)
    return {"analysis_id": analysis_id, **gap}

@app.get("/api/agent-logs/{analysis_id}")
def agent_logs(analysis_id: str):
    result = ANALYSES.get(analysis_id) or get_analysis(analysis_id)
    if not result: raise HTTPException(status_code=404, detail="Analysis not found")
    return {"analysis_id": analysis_id, "logs": result.get("logs", [])}

@app.post("/api/assistant")
def assistant(payload: AssistantIn):
    analysis = (ANALYSES.get(payload.analysis_id) if payload.analysis_id else None) or (get_analysis(payload.analysis_id) if payload.analysis_id else None)
    profile = parse_profile((payload.profile or ProfileIn(**PROFILE)).model_dump())
    return {"reply": assistant_reply(payload.message, profile, analysis)}

@app.post("/api/feedback")
def feedback(payload: dict[str, Any]): return {"ok": True, "message": "Thanks for helping us improve SkillPath AI."}

@app.get("/api/dashboard")
def dashboard():
    return {"profile": PROFILE, "stats": {"jobs": len(JOBS), "courses": len(COURSES), "skills": 28, "match": 72}, "top_matches": match_jobs(PROFILE)[:3]}
