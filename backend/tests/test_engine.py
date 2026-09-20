from app.engine import build_gap, match_jobs, normalize_skill, parse_profile, select_target_job
from app.data import DEFAULT_PROFILE, JOBS

def test_skill_normalization():
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("React.js") == "React"

def test_matching_is_reproducible():
    profile = parse_profile(DEFAULT_PROFILE)
    first, second = match_jobs(profile), match_jobs(profile)
    assert len(first) == len(JOBS)
    assert [x["score"] for x in first] == [x["score"] for x in second]
    assert all("semantic_similarity" in x for x in first)

def test_gap_and_free_path():
    profile = parse_profile(DEFAULT_PROFILE)
    job = match_jobs(profile)[0]
    gap = build_gap(job, profile, free_only=True)
    assert gap["total_cost"] == 0
    assert gap["total_weeks"] >= 0
    assert gap["coverage_after"]["covered"] >= gap["coverage_before"]["covered"]


def test_profiles_rank_their_own_career_domains():
    profiles = {
        "electrical": {"skills": ["Circuit Analysis", "MATLAB", "AutoCAD", "Power Systems"], "interests": ["Electrical Engineering", "Electronics"], "target_role": "Electrical Engineer"},
        "software": {"skills": ["Python", "React", "FastAPI", "SQL", "Git"], "interests": ["Software Engineering", "Web Development"], "target_role": "Full Stack Developer"},
        "finance": {"skills": ["Financial Analysis", "Excel", "Accounting"], "interests": ["Finance", "MBA", "Management"], "target_role": "Financial Analyst"},
    }
    ranked = {name: match_jobs(parse_profile(profile)) for name, profile in profiles.items()}

    assert {job["domain"] for job in ranked["electrical"][:2]} <= {"Electrical", "Electronics"}
    assert all(job["domain"] == "Software/IT" for job in ranked["software"][:3])
    assert {job["domain"] for job in ranked["finance"][:3]} <= {"Finance", "Accounting", "MBA/Management"}
    assert ranked["electrical"][0]["id"] != ranked["software"][0]["id"]
    assert ranked["finance"][0]["id"] != ranked["software"][0]["id"]


def test_job_catalog_covers_requested_domains():
    required_domains = {"Software/IT", "Electrical", "Electronics", "Mechanical", "Civil", "Chemical", "MBA/Management", "Finance", "Accounting", "Marketing", "HR", "AI/Data", "Healthcare", "Design"}
    assert len(JOBS) >= 40
    assert required_domains <= {job["domain"] for job in JOBS}
    assert all(job["required_skills"] and job["preferred_skills"] and job["interests"] for job in JOBS)


def test_vlsi_profile_selects_electronics_target():
    profile = parse_profile({
        "education": "B.E. Electronics and Communication Engineering",
        "skills": ["VLSI & Digital Design"],
        "location": "Bengaluru",
        "interests": ["Electronics Engineer"],
        "target_role": "Electronics Engineer",
        "experience": "Student / Fresher",
    })
    matches = match_jobs(profile)
    target = select_target_job(matches, profile)

    assert target is not None
    assert target["domain"] == "Electronics"
    assert "VLSI" in target["title"]
    assert target["id"] != "job-36"
