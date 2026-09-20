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
    "mba": "MBA", "hr": "HR", "ai": "AI", "ux": "UX Design", "ui": "UX Design", "mlops": "MLOps",
}

CAREER_DOMAIN_TERMS = {
    "software_it": {"software", "software engineering", "software engineer", "developer", "development", "full stack", "frontend", "backend", "web development", "programming", "java", "javascript", "python", "react", "fastapi", "sql", "devops", "cloud", "cybersecurity"},
    "ai_data": {"ai", "artificial intelligence", "machine learning", "data", "data science", "data analytics", "analytics", "nlp", "computer vision", "statistics"},
    "electronics": {"electronics", "electronics engineer", "vlsi", "vlsi & digital design", "digital design", "digital electronics", "embedded systems", "microcontrollers", "fpga", "verilog", "systemverilog", "pcb design", "signal processing"},
    "electrical": {"electrical", "electrical engineering", "electrical engineer", "power systems", "power engineering", "circuit analysis", "matlab", "plc", "scada", "control systems", "electrical machines"},
    "mechanical": {"mechanical", "mechanical engineering", "mechanical engineer", "mechanical design", "cad", "solidworks", "catia", "manufacturing", "tolerance analysis", "lean manufacturing"},
    "civil": {"civil", "civil engineering", "civil engineer", "structural", "structural analysis", "construction", "reinforced concrete", "surveying", "autocad"},
    "chemical": {"chemical", "chemical engineering", "chemical engineer", "process design", "process engineering", "mass balance", "pfd", "hse", "safety engineering"},
    "finance": {"finance", "financial", "financial analysis", "financial analyst", "valuation", "forecasting", "corporate finance"},
    "accounting": {"accounting", "accountant", "tally", "financial reporting", "gst", "taxation", "audit"},
    "mba_management": {"mba", "management", "business management", "business analysis", "business analyst", "product management", "operations management", "strategy"},
    "marketing": {"marketing", "brand strategy", "market research", "content strategy", "seo", "growth"},
    "hr": {"hr", "human resources", "talent acquisition", "recruitment", "employee relations", "hr analytics"},
    "healthcare": {"healthcare", "healthcare administration", "patient care", "hospital", "clinical", "medical"},
    "design": {"design", "ux", "ux design", "ui", "visual design", "user research", "figma", "prototyping", "interaction design"},
    "research": {"research", "research methodology", "research engineer"},
}

def career_domains(*values: Any) -> set[str]:
    text = " ".join(str(value) for value in values if value).lower()
    domains: set[str] = set()
    for domain, terms in CAREER_DOMAIN_TERMS.items():
        if any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) for term in terms):
            domains.add(domain)
    return domains

def job_domains(job: dict[str, Any]) -> set[str]:
    return career_domains(job.get("domain", ""), job.get("title", ""), job.get("required_skills", []), job.get("preferred_skills", []), job.get("interests", []))

def normalize_skill(value: str) -> str:
    raw = re.sub(r"\s+", " ", value.strip())
    if not raw:
        return ""

    lowered = raw.lower()
    if lowered in ALIASES:
        return ALIASES[lowered]

    if raw.upper() in {"MBA", "HR", "AI", "ML", "SQL", "HTML", "CSS", "AWS", "NLP", "UX", "UI"}:
        return raw.upper()

    return raw.title() if raw.lower() not in {"sql", "html", "css", "git", "aws", "nlp", "ai", "ui", "ux"} else raw.upper()

def canonical_skill_key(value: str) -> str:
    """Return the one comparison key used for all skill matching and coverage."""
    return re.sub(r"\s+", " ", normalize_skill(value)).strip().casefold()

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
        b = model.encode(" ".join([job["title"], job.get("domain", ""), *job["required_skills"], *job["preferred_skills"], *job["interests"]]), convert_to_tensor=True)
        return round(max(0.0, min(1.0, float(util.cos_sim(a, b)[0][0]))), 4)
    except Exception:
        a, b = tokenize(profile_text), tokenize(" ".join([job["title"], job.get("domain", ""), *job["required_skills"], *job["preferred_skills"], *job["interests"]]))
        return round(len(a & b) / max(1, len(a | b)), 4)

@lru_cache(maxsize=1)
def _embedding_model() -> Any:
    from sentence_transformers import SentenceTransformer  # type: ignore
    return SentenceTransformer("all-MiniLM-L6-v2")

def parse_profile(profile: dict[str, Any] | None = None, resume_text: str = "") -> dict[str, Any]:
    if profile is None:
        incoming = {**DEFAULT_PROFILE}
    else:
        incoming = {
            "name": profile.get("name", "Demo User"),
            "education": profile.get("education", ""),
            "skills": profile.get("skills", []),
            "location": profile.get("location", ""),
            "interests": profile.get("interests", []),
            "target_role": profile.get("target_role", ""),
            "experience": profile.get("experience", ""),
            "resume_text": resume_text or profile.get("resume_text", ""),
        }

    text = incoming.get("resume_text", "")
    skills = normalize_skills(incoming.get("skills"))

    known_skills = {
        normalize_skill(skill)
        for job in JOBS
        for skill in [*job["required_skills"], *job["preferred_skills"]]
    }
    for skill in sorted(known_skills, key=len, reverse=True):
        if skill.lower() in text.lower() and skill not in skills:
            skills.append(skill)

    incoming["skills"] = skills
    incoming["resume_text"] = resume_text or incoming.get("resume_text", "")
    return incoming

def match_jobs(profile: dict[str, Any], jobs: list[dict[str, Any]] = JOBS) -> list[dict[str, Any]]:
    print("MATCH ENGINE VERSION: DOMAIN-FIX-V2", flush=True)
    print("PROFILE:", profile, flush=True)
    print("TARGET:", profile.get("target_role"), flush=True)
    skills = set(normalize_skills(profile.get("skills")))
    interests = {normalize_skill(str(x)).lower() for x in profile.get("interests", [])}
    location = str(profile.get("location", "")).lower()
    target_role = str(profile.get("target_role", ""))
    education = str(profile.get("education", ""))
    profile_domains = career_domains(target_role, profile.get("interests", []), profile.get("skills", []), education)
    profile_text = " ".join([target_role, education, str(profile.get("experience", "")), *skills, *interests, *(domain.replace("_", " ") for domain in sorted(profile_domains)), str(profile.get("resume_text", ""))])
    results = []
    for job in jobs:
        required = list(job["required_skills"]); preferred = list(job["preferred_skills"])
        skill_keys = {canonical_skill_key(skill) for skill in skills}
        required_keys = {canonical_skill_key(skill) for skill in required}
        preferred_keys = {canonical_skill_key(skill) for skill in preferred}
        matched = [skill for skill in required if canonical_skill_key(skill) in skill_keys]
        missing = [skill for skill in required if canonical_skill_key(skill) not in skill_keys]
        matched_pref = [skill for skill in preferred if canonical_skill_key(skill) in skill_keys]
        missing_pref = [skill for skill in preferred if canonical_skill_key(skill) not in skill_keys]
        skill_score = (len(matched) + 0.5 * len(matched_pref)) / max(1, len(required) + 0.5 * len(preferred))
        semantic = semantic_similarity(profile_text, {**job, "domain": " ".join(domain.replace("_", " ") for domain in sorted(job_domains(job)))})
        location_score = 1.0 if location and location in job["location"].lower() else 0.45
        job_interests = {normalize_skill(str(x)).lower() for x in job["interests"]}
        explicit_interest_score = len(interests & job_interests) / max(1, min(len(interests), len(job_interests)))
        domain_score = 1.0 if profile_domains & job_domains(job) else 0.0
        interest_score = max(explicit_interest_score, domain_score)
        score = round(100 * (skill_score * .4 + semantic * .4 + location_score * .1 + interest_score * .1))
        results.append({**job, "score": score, "skill_score": round(skill_score * 100), "semantic_similarity": round(semantic * 100), "location_compatibility": round(location_score * 100), "interest_compatibility": round(interest_score * 100), "matched_skills": matched, "missing_skills": missing, "matched_preferred_skills": matched_pref, "missing_preferred_skills": missing_pref})
    return sorted(results, key=lambda x: (-x["score"], x["id"]))

def select_target_job(matches: list[dict[str, Any]], profile: dict[str, Any], job_id: str | None = None) -> dict[str, Any] | None:
    if not matches:
        return None
    if job_id:
        selected = next((job for job in matches if job["id"] == job_id), None)
        if selected:
            return selected

    target_role = normalize_skill(str(profile.get("target_role", ""))).lower()
    if target_role:
        exact = [job for job in matches if target_role in normalize_skill(job["title"]).lower()]
        if exact:
            return exact[0]

    return max(matches, key=lambda job: (job["score"], job["semantic_similarity"], job["interest_compatibility"], job["skill_score"]))

def course_for_skill(skill: str, free_only: bool = False) -> dict[str, Any] | None:
    target_key = canonical_skill_key(skill)
    candidates = []
    for course in COURSES:
        if free_only and not course["is_free"]:
            continue
        taught_keys = {canonical_skill_key(taught) for taught in course["skills_taught"]}
        exact = int(target_key in taught_keys)
        title_exact = int(target_key in canonical_skill_key(course.get("title", "")))
        if not exact and not title_exact:
            continue
        candidates.append((course, exact, title_exact))

    ranked = sorted(
        candidates,
        key=lambda item: (
            -item[1],
            -item[2],
            not item[0]["is_free"],
            item[0]["duration"],
            item[0]["cost"],
            item[0]["id"],
        ),
    )
    return ranked[0][0] if ranked else None

def build_gap(job: dict[str, Any], profile: dict[str, Any], free_only: bool = False) -> dict[str, Any]:
    skills = {canonical_skill_key(skill) for skill in profile.get("skills", [])}
    required = list(job["required_skills"]); preferred = list(job["preferred_skills"])
    missing = [skill for skill in required if canonical_skill_key(skill) not in skills]
    missing_pref = [skill for skill in preferred if canonical_skill_key(skill) not in skills]
    gaps = []
    for skill in missing + missing_pref:
        course = course_for_skill(skill, free_only)
        is_required = skill in missing
        fallback = f"{skill} is listed as a { 'core' if is_required else 'supporting' } requirement for {job['title']}."
        gaps.append({"skill": skill, "requirement": "Required" if is_required else "Preferred", "why": explain_gap(job["title"], skill, fallback), "status": "Missing", "priority": "High" if is_required else "Medium", "next_step": f"Complete a practical {skill} module and add a portfolio example.", "resource": course})
    unique_courses = []
    seen = set()
    for gap in gaps:
        if gap["resource"] and gap["resource"]["id"] not in seen: unique_courses.append(gap["resource"]); seen.add(gap["resource"]["id"])
    total_weeks = sum(c["duration"] if c["duration_unit"] == "weeks" else c["duration"] / 7 for c in unique_courses)
    total_cost = sum(c["cost"] for c in unique_courses)
    before = len([skill for skill in required if canonical_skill_key(skill) in skills])
    after = before + len([skill for skill in missing if any(canonical_skill_key(skill) == canonical_skill_key(taught) for course in unique_courses for taught in course["skills_taught"])])
    return {"missing_required_skills": missing, "missing_preferred_skills": missing_pref, "gaps": gaps, "resources": unique_courses, "total_weeks": round(total_weeks, 1), "total_cost": total_cost, "currency": "INR", "coverage_before": {"covered": before, "total": len(required)}, "coverage_after": {"covered": after, "total": len(required)}, "weekly_study_hours": 8, "roi_reasoning": f"{round(total_weeks, 1)} weeks of learning closes {after - before} required skill gaps at ₹{total_cost:,} using {'free' if free_only else 'free and paid'} resources."}

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
            graph.add_node("gap_analysis", lambda s: {**s, "target": select_target_job(s["matches"], s["parsed"], s.get("job_id"))})
            graph.add_node("training_recommendation", lambda s: {**s, "gap": build_gap(s["target"], s["parsed"], s["free_only"]) if s.get("target") else None})
            graph.add_node("roadmap", lambda s: s)
            graph.add_edge(START, "profile_parsing"); graph.add_edge("profile_parsing", "job_matching"); graph.add_edge("job_matching", "gap_analysis"); graph.add_edge("gap_analysis", "training_recommendation"); graph.add_edge("training_recommendation", "roadmap"); graph.add_edge("roadmap", END)
            state = graph.compile().invoke(state)
        else:
            state["parsed"] = parse_profile(profile, profile.get("resume_text", "")); state["matches"] = match_jobs(state["parsed"]); state["target"] = select_target_job(state["matches"], state["parsed"], job_id); state["gap"] = build_gap(state["target"], state["parsed"], free_only) if state.get("target") else None
        self.log("Profile Parsing Agent", "Normalized profile skills and extracted target role")
        self.log("Job Matching Agent", f"Evaluated {len(state.get('matches', []))} curated jobs with deterministic scoring")
        target, gap = state.get("target"), state.get("gap")
        if not target: return {"id": self.analysis_id, "profile": state["parsed"], "matches": [], "logs": self.logs}
        self.log("Gap Analysis Agent", f"Identified {len(gap['missing_required_skills'])} required and {len(gap['missing_preferred_skills'])} preferred gaps")
        self.log("Training Recommendation Agent", f"Mapped {len(gap['resources'])} unique learning resources to gaps")
        self.log("Time-to-Ready/Roadmap Engine", f"Calculated {gap['total_weeks']} weeks and ₹{gap['total_cost']} total cost")
        return {"id": self.analysis_id, "profile": state["parsed"], "target_job": target, "matches": state["matches"][:12], "gap_analysis": gap, "logs": self.logs, "created_at": datetime.now(timezone.utc).isoformat(), "orchestrator": "LangGraph" if LANGGRAPH_AVAILABLE else "deterministic LangGraph-compatible fallback"}
