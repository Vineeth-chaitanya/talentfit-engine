from app.core.resume_extractor import extract_resume
from app.core.job_extractor import extract_job
from app.core.matcher import match_candidate_to_job


def test_score_range_and_missing_skills():
    resume = extract_resume("Skills: Python, FastAPI, Docker. Experience: Built REST API services.")
    job = extract_job("Required: Python, FastAPI, Kubernetes. Preferred: Docker.")
    result = match_candidate_to_job(resume, job)
    assert 0 <= result.final_score <= 100
    assert "Kubernetes" in result.missing_required_skills
    assert "Python" in result.matched_skills
