from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from .data import COURSES, DEFAULT_PROFILE, JOBS
from .llm import explain_gap

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript", "react.js": "React", "reactjs": "React",
    "react": "React", "html5": "HTML", "css3": "CSS", "postgres": "SQL", "postgresql": "SQL",
    "fast api": "FastAPI", "fastapi": "FastAPI", "rest": "REST APIs", "rest api": "REST APIs", "ml": "Machine Learning",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "k8s": "Kubernetes", "a/b testing": "A/B Testing",
}

def normalize_skill(value: str) -> str:
    raw = re.sub(r"\s+", " ", value.strip())
    return ALIASES.get(raw.lower(), raw.title() if raw.lower() not in {"sql", "html", "css", "git", "aws", "nlp"} else raw.upper())

def normalize_skills(values: list[str] | str | None) -> list[str]:
    if not values: return []
    if isinstance(values, str): values = re.split(r",|\n|;", values)
    result: list[str] = []
    for item in values:
        normalized = normalize_skill(str(item))
        if normalized and normalized not in result: result.append(normalized)
    return result

def tokenize(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-zA-Z][a-zA-Z+#.\-/]{1,}", text.lower()) if len(x) > 2}

def semantic_similarity(profile_text: str, job: dict[str, Any]) -> float:
    """Deterministic lexical fallback; uses SentenceTransformer when installed."""
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
        model = _embedding_model()
        a = model.encode(profile_text, convert_to_tensor=True)
        b = model.encode(" ".join([job["title"], *job["required_skills"], *job["interests"]]), convert_to_tensor=True)
        return round(max(0.0, min(1.0, float(util.cos_sim(a, b)[0][0]))), 4)
    except Exception:
        a, b = tokenize(profile_text), tokenize(" ".join([job["title"], *job["required_skills"], *job["interests"]]))
        return round(len(a & b) / max(1, len(a | b)), 4)

@lru_cache(maxsize=1)
def _embedding_model() -> Any:
    from sentence_transformers import SentenceTransformer  # type: ignore
    return SentenceTransformer("all-MiniLM-L6-v2")

def parse_profile(profile: dict[str, Any] | None = None, resume_text: str = "") -> dict[str, Any]:
    incoming = {**DEFAULT_PROFILE, **(profile or {})}
    text = " ".join(str(v) for v in incoming.values()) + " " + resume_text
    skills = normalize_skills(incoming.get("skills"))
    known = ["Python", "JavaScript", "React", "HTML", "CSS", "SQL", "Git", "FastAPI", "Docker", "AWS", "Machine Learning", "TensorFlow", "PyTorch", "Kubernetes", "Power BI", "Statistics", "Excel", "REST APIs", "TypeScript", "Testing", "Linux", "CI/CD", "Analytics", "A/B Testing", "NLP", "Pandas", "OpenCV", "Communication"]
    lower = text.lower()
    for skill in known:
        if skill.lower() in lower and skill not in skills: skills.append(skill)
    incoming["skills"] = skills
    incoming["resume_text"] = resume_text or incoming.get("resume_text", "")
    return incoming

def match_jobs(profile: dict[str, Any], jobs: list[dict[str, Any]] = JOBS) -> list[dict[str, Any]]:
    skills = set(normalize_skills(profile.get("skills")))
    interests = {str(x).lower() for x in profile.get("interests", [])}
    location = str(profile.get("location", "")).lower()
    profile_text = " ".join([str(profile.get("target_role", "")), str(profile.get("experience", "")), *skills, *interests, str(profile.get("resume_text", ""))])
    results = []
    for job in jobs:
        required = normalize_skills(job["required_skills"]); preferred = normalize_skills(job["preferred_skills"])
        matched = [x for x in required if x in skills]; missing = [x for x in required if x not in skills]
        matched_pref = [x for x in preferred if x in skills]; missing_pref = [x for x in preferred if x not in skills]
        skill_score = (len(matched) + 0.5 * len(matched_pref)) / max(1, len(required) + 0.5 * len(preferred))
        semantic = semantic_similarity(profile_text, job)
        location_score = 1.0 if location and location in job["location"].lower() else 0.45
        interest_score = min(1.0, len(interests & {x.lower() for x in job["interests"]}) / max(1, len(job["interests"])))
        score = round(100 * (skill_score * .4 + semantic * .4 + location_score * .1 + interest_score * .1))
        results.append({**job, "score": score, "skill_score": round(skill_score * 100), "semantic_similarity": round(semantic * 100), "location_compatibility": round(location_score * 100), "interest_compatibility": round(interest_score * 100), "matched_skills": matched, "missing_skills": missing, "matched_preferred_skills": matched_pref, "missing_preferred_skills": missing_pref})
    return sorted(results, key=lambda x: (-x["score"], x["id"]))

def course_for_skill(skill: str, free_only: bool = False) -> dict[str, Any] | None:
    matches = [c for c in COURSES if skill in c["skills_taught"] and (not free_only or c["is_free"])]
    return sorted(matches, key=lambda c: (not c["is_free"], c["duration"], c["cost"]))[0] if matches else None

def build_gap(job: dict[str, Any], profile: dict[str, Any], free_only: bool = False) -> dict[str, Any]:
    skills = set(normalize_skills(profile.get("skills"))); missing = [s for s in job["required_skills"] if s not in skills]; missing_pref = [s for s in job["preferred_skills"] if s not in skills]
    gaps = []
    for skill in missing + missing_pref:
        course = course_for_skill(skill, free_only)
        required = skill in missing
        fallback = f"{skill} is listed as a { 'core' if required else 'supporting' } requirement for {job['title']}."
        gaps.append({"skill": skill, "requirement": "Required" if required else "Preferred", "why": explain_gap(job["title"], skill, fallback), "status": "Missing", "priority": "High" if required else "Medium", "next_step": f"Complete a practical {skill} module and add a portfolio example.", "resource": course})
    unique_courses = []
    seen = set()
    for gap in gaps:
        if gap["resource"] and gap["resource"]["id"] not in seen: unique_courses.append(gap["resource"]); seen.add(gap["resource"]["id"])
    total_weeks = sum(c["duration"] if c["duration_unit"] == "weeks" else c["duration"] / 7 for c in unique_courses)
    total_cost = sum(c["cost"] for c in unique_courses)
    before = len([s for s in job["required_skills"] if s in skills]); after = before + len([s for s in missing if any(s in c["skills_taught"] for c in unique_courses)])
    return {"missing_required_skills": missing, "missing_preferred_skills": missing_pref, "gaps": gaps, "resources": unique_courses, "total_weeks": round(total_weeks, 1), "total_cost": total_cost, "currency": "INR", "coverage_before": {"covered": before, "total": len(job["required_skills"])}, "coverage_after": {"covered": after, "total": len(job["required_skills"])}, "weekly_study_hours": 8, "roi_reasoning": f"{round(total_weeks, 1)} weeks of learning closes {after - before} required skill gaps at ₹{total_cost:,} using {'free' if free_only else 'free and paid'} resources."}

@dataclass
class Workflow:
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    logs: list[dict[str, Any]] = field(default_factory=list)
    def log(self, agent: str, message: str, status: str = "completed") -> None:
        self.logs.append({"agent": agent, "message": message, "status": status, "timestamp": datetime.now(timezone.utc).isoformat()})
    def run(self, profile: dict[str, Any], job_id: str | None = None, free_only: bool = False) -> dict[str, Any]:
        state: dict[str, Any] = {"profile": profile, "job_id": job_id, "free_only": free_only}
        if LANGGRAPH_AVAILABLE:
            graph = StateGraph(dict)
            graph.add_node("profile_parsing", lambda s: {**s, "parsed": parse_profile(s["profile"], s["profile"].get("resume_text", ""))})
            graph.add_node("job_matching", lambda s: {**s, "matches": match_jobs(s["parsed"])})
            graph.add_node("gap_analysis", lambda s: {**s, "target": next((j for j in s["matches"] if j["id"] == s.get("job_id")), s["matches"][0] if s["matches"] else None)})
            graph.add_node("training_recommendation", lambda s: {**s, "gap": build_gap(s["target"], s["parsed"], s["free_only"]) if s.get("target") else None})
            graph.add_node("roadmap", lambda s: s)
            graph.add_edge(START, "profile_parsing"); graph.add_edge("profile_parsing", "job_matching"); graph.add_edge("job_matching", "gap_analysis"); graph.add_edge("gap_analysis", "training_recommendation"); graph.add_edge("training_recommendation", "roadmap"); graph.add_edge("roadmap", END)
            state = graph.compile().invoke(state)
        else:
            state["parsed"] = parse_profile(profile, profile.get("resume_text", "")); state["matches"] = match_jobs(state["parsed"]); state["target"] = next((j for j in state["matches"] if j["id"] == job_id), state["matches"][0] if state["matches"] else None); state["gap"] = build_gap(state["target"], state["parsed"], free_only) if state.get("target") else None
        self.log("Profile Parsing Agent", "Normalized profile skills and extracted target role")
        self.log("Job Matching Agent", f"Evaluated {len(state.get('matches', []))} curated jobs with deterministic scoring")
        target, gap = state.get("target"), state.get("gap")
        if not target: return {"id": self.analysis_id, "profile": state["parsed"], "matches": [], "logs": self.logs}
        self.log("Gap Analysis Agent", f"Identified {len(gap['missing_required_skills'])} required and {len(gap['missing_preferred_skills'])} preferred gaps")
        self.log("Training Recommendation Agent", f"Mapped {len(gap['resources'])} unique learning resources to gaps")
        self.log("Time-to-Ready/Roadmap Engine", f"Calculated {gap['total_weeks']} weeks and ₹{gap['total_cost']} total cost")
        return {"id": self.analysis_id, "profile": state["parsed"], "target_job": target, "matches": state["matches"][:12], "gap_analysis": gap, "logs": self.logs, "created_at": datetime.now(timezone.utc).isoformat(), "orchestrator": "LangGraph" if LANGGRAPH_AVAILABLE else "deterministic LangGraph-compatible fallback"}
