# Senior ML Engineer Review Notes

## Main credibility risks found

1. **Overclaiming risk: LLM/AI wording**
   - The core MVP is deterministic and local-first, not an LLM-powered parser.
   - README language was revised to say optional LLM extraction is future work, not a current core dependency.

2. **Evaluation risk: tiny labeled set**
   - The evaluation is useful as a smoke test but too small to claim model quality.
   - README and eval scripts now explicitly call it a smoke evaluation, not a benchmark.

3. **Scoring risk: manual weights**
   - The score is not trained or calibrated.
   - README now frames the score as an interpretable heuristic and explains how it should be calibrated in production.

4. **Evidence fragility**
   - The original evidence extraction could miss evidence when the resume used an alias, such as `sklearn` for `scikit-learn`.
   - Evidence extraction now checks canonical skills and aliases.

5. **Years-of-experience regex bug**
   - The original regex had an invalid word boundary character.
   - It now uses a proper `\b` boundary and has unit coverage.

6. **Required/preferred skill parsing fragility**
   - Job parsing remains heuristic and can misclassify messy postings.
   - README now states this limitation directly.

7. **Repository hygiene**
   - Cached Python files and pytest cache were removed from the packaged project.
   - `.gitignore` was tightened.

## How to defend this project in an interview

- Do not say it “uses AI to perfectly screen candidates.”
- Say it is an explainable local-first matching system that combines normalized skill coverage, semantic similarity, keyword similarity, and evidence-based suggestions.
- Emphasize tradeoffs: deterministic extraction is auditable but lower recall than a well-designed LLM extraction pipeline.
- Explain that the current evaluation demonstrates methodology, while production evaluation would require a larger labeled dataset and calibration against recruiter feedback.
