---
name: run-labor-code-evaluation
description: Use when asked how the labor-code assistant performs, to score it, or to review its golden set. Runs the deterministic and judge evaluation and explains the metrics and limitations.
---

# Run the labor-code evaluation

1. Confirm `data/labor_code.json` exists; if not, run `python src/fetch_law.py`.
2. Confirm model access is configured without reading or displaying `.env`.
3. Run `python src/evaluate_golden_set.py`. This makes a model call for each
   case and a separate judge call for each answer.
4. Read every answer in `evaluation/golden_results.json`; do not present
   automated checks as a substitute for human review.
5. Report the number of cases, deterministic citation/retrieval results,
   abstention results, and judge verdicts. State that results cover only this
   golden set and the recorded source snapshot.
6. After human reviewers label the drafts in `evaluation/draft_labels.csv`,
   run `python src/evaluate_judge.py` to report judge TPR and TNR. Do not
   fabricate or infer missing human labels.
