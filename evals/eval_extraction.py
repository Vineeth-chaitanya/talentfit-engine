"""Small, transparent extraction evaluation.

This is not a benchmark. It is a repeatable smoke evaluation showing how the
taxonomy-based extractor behaves on labeled examples. A real production system would
need a larger, role-diverse, independently labeled dataset.
"""

import json
from pathlib import Path
from statistics import mean
from app.core.resume_extractor import extract_resume

ROOT = Path(__file__).resolve().parents[1]


def prf(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    tp = len(pred & gold)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def main():
    examples = json.loads((ROOT / "evals/labeled_examples.json").read_text())
    rows = []
    for ex in examples:
        text = ex.get("resume_text") or (ROOT / ex["resume_path"]).read_text()
        pred = set(extract_resume(text).skills)
        gold = set(ex["expected_resume_skills"])
        p, r, f = prf(pred, gold)
        rows.append({
            "id": ex["id"],
            "precision": round(p, 3),
            "recall": round(r, 3),
            "f1": round(f, 3),
            "false_positives": sorted(pred - gold),
            "false_negatives": sorted(gold - pred),
        })
    summary = {
        "macro_precision": round(mean(r["precision"] for r in rows), 3),
        "macro_recall": round(mean(r["recall"] for r in rows), 3),
        "macro_f1": round(mean(r["f1"] for r in rows), 3),
        "n_examples": len(rows),
    }
    print(json.dumps({"summary": summary, "examples": rows}, indent=2))


if __name__ == "__main__":
    main()
