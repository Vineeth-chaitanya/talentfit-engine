"""Matching sanity checks.

The expected score ranges are intentionally broad because the score is a heuristic,
not a trained probability. These checks catch regressions such as a strong match
scoring very low or a weak match scoring unrealistically high.
"""

import json
import time
from pathlib import Path
from statistics import mean
from app.core.resume_extractor import extract_resume
from app.core.job_extractor import extract_job
from app.core.matcher import match_candidate_to_job

ROOT = Path(__file__).resolve().parents[1]


def main():
    examples = json.loads((ROOT / "evals/labeled_examples.json").read_text())
    results = []
    for ex in examples:
        resume_text = ex.get("resume_text") or (ROOT / ex["resume_path"]).read_text()
        job_text = ex.get("job_text") or (ROOT / ex["job_path"]).read_text()
        start = time.perf_counter()
        result = match_candidate_to_job(extract_resume(resume_text), extract_job(job_text))
        latency_ms = (time.perf_counter() - start) * 1000
        passed = ex["expected_score_min"] <= result.final_score <= ex["expected_score_max"]
        results.append({
            "id": ex["id"],
            "score": result.final_score,
            "expected_range": [ex["expected_score_min"], ex["expected_score_max"]],
            "latency_ms": round(latency_ms, 2),
            "sanity_check_passed": passed,
            "missing_required_skills": result.missing_required_skills,
        })
    summary = {
        "n_examples": len(results),
        "pass_rate": round(sum(r["sanity_check_passed"] for r in results) / len(results), 3),
        "avg_latency_ms": round(mean(r["latency_ms"] for r in results), 2),
    }
    print(json.dumps({"summary": summary, "examples": results}, indent=2))


if __name__ == "__main__":
    main()
