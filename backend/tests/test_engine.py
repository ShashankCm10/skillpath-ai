from app.engine import build_gap, match_jobs, normalize_skill, parse_profile
from app.data import DEFAULT_PROFILE, JOBS

def test_skill_normalization():
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("React.js") == "React"

def test_matching_is_reproducible():
    profile = parse_profile(DEFAULT_PROFILE)
    first, second = match_jobs(profile), match_jobs(profile)
    assert len(first) == 40
    assert [x["score"] for x in first] == [x["score"] for x in second]
    assert all("semantic_similarity" in x for x in first)

def test_gap_and_free_path():
    profile = parse_profile(DEFAULT_PROFILE)
    job = match_jobs(profile)[0]
    gap = build_gap(job, profile, free_only=True)
    assert gap["total_cost"] == 0
    assert gap["total_weeks"] >= 0
    assert gap["coverage_after"]["covered"] >= gap["coverage_before"]["covered"]
