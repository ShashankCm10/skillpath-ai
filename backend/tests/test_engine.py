from app.engine import build_gap, career_domains, course_for_skill, match_jobs, normalize_skill, parse_profile, select_target_job
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


def test_career_domains_and_supplied_profile_do_not_inherit_defaults():
    profile = parse_profile({
        "education": "B.E. Electronics and Communication Engineering",
        "skills": ["VLSI & Digital Design", "MATLAB"],
        "location": "Bengaluru",
        "interests": ["Electronics Engineer"],
        "target_role": "Electronics Engineer",
    })

    assert career_domains(profile["target_role"], profile["interests"], profile["skills"], profile["education"]) >= {"electronics"}
    assert profile["skills"] == ["Vlsi & Digital Design", "Matlab"]
    assert "Python" not in profile["skills"]
    assert "JavaScript" not in profile["skills"]
    assert "FastAPI" not in profile["skills"]


def test_electronics_training_maps_all_vlsi_gaps_and_free_only_recalculates():
    profile = parse_profile({
        "education": "B.E. Electronics and Communication Engineering",
        "skills": ["VLSI & Digital Design", "MATLAB"],
        "location": "Bengaluru",
        "interests": ["Electronics Engineer"],
        "target_role": "Electronics Engineer",
    })
    job = match_jobs(profile)[0]
    paid = build_gap(job, profile)
    free = build_gap(job, profile, free_only=True)

    assert job["title"] == "VLSI Design Engineer"
    assert paid["resources"]
    assert paid["total_weeks"] > 0
    assert paid["total_cost"] > free["total_cost"]
    assert paid["total_weeks"] > free["total_weeks"]
    assert "VLSI & Digital Design" not in paid["missing_required_skills"]
    assert {gap["skill"] for gap in paid["gaps"]} >= {"Digital Electronics", "Verilog", "Circuit Analysis", "SystemVerilog", "FPGA"}
    assert all(resource["is_free"] for resource in free["resources"])


def test_training_course_matching_is_canonical_and_domain_aware():
    assert course_for_skill("Vlsi")
    assert course_for_skill("MATLAB")
    assert course_for_skill("FPGA")
    assert "Verilog" in course_for_skill("Verilog")["skills_taught"]
    assert "SystemVerilog" in course_for_skill("SystemVerilog")["skills_taught"]
    assert course_for_skill("SystemVerilog")["title"] != "PCB Design Fundamentals"
    assert "Financial Analysis" in course_for_skill("Financial Analysis")["skills_taught"]

    software = parse_profile({"skills": ["Python", "React", "FastAPI", "SQL"], "target_role": "Full Stack Developer", "interests": ["Software Engineering"]})
    software_gap = build_gap(match_jobs(software)[0], software)

    assert any("Python" in resource["skills_taught"] or "JavaScript" in resource["skills_taught"] for resource in software_gap["resources"])
    finance_course = course_for_skill("Financial Analysis")
    assert "Financial Analysis" in finance_course["skills_taught"] or "Accounting" in finance_course["skills_taught"]
