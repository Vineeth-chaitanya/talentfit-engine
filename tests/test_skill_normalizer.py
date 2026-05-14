from app.core.skill_normalizer import get_skill_normalizer


def test_synonym_normalization():
    n = get_skill_normalizer()
    assert n.normalize_skill("Postgres") == "PostgreSQL"
    assert n.normalize_skill("sklearn") == "scikit-learn"
    assert n.normalize_skill("gen ai") == "Generative AI"
    assert n.normalize_skill("vector db") == "Vector Database"
    assert n.normalize_skill("PowerBI") == "Power BI"


def test_extract_skills():
    n = get_skill_normalizer()
    found = n.extract_skills("Built a Fast API service using sklearn and Postgres.")
    assert "FastAPI" in found
    assert "scikit-learn" in found
    assert "PostgreSQL" in found
