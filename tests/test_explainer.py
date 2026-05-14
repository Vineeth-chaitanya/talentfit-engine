from app.core.resume_extractor import extract_resume
from app.core.job_extractor import extract_job
from app.core.matcher import match_candidate_to_job
from app.core.explainer import generate_fit_report


def test_evidence_snippet_extraction_and_report():
    candidate = extract_resume("""Skills
Python, FastAPI
Projects
Built a FastAPI service for NLP matching.""")
    job = extract_job("Required: FastAPI and NLP.")
    result = match_candidate_to_job(candidate, job)
    report = generate_fit_report(candidate, job, result)
    assert "Overall Fit" in report
    assert any(e.skill == "FastAPI" for e in candidate.evidence)
