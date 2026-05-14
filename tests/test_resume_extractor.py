from app.core.resume_extractor import extract_resume


def test_alias_evidence_and_years_extraction():
    candidate = extract_resume("""Summary
Machine learning engineer with 3+ years of experience.
Skills
Built models with sklearn and stored features in Postgres.
""")
    assert candidate.experience_years == 3
    assert "scikit-learn" in candidate.skills
    assert "PostgreSQL" in candidate.skills
    assert any(e.skill == "scikit-learn" and "sklearn" in e.snippet for e in candidate.evidence)
