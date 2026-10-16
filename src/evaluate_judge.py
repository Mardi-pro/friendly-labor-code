"""Compare the model judge with hand labels from the evaluation traces."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = ROOT / "evaluation" / "draft_labels.csv"
RESULTS_PATH = ROOT / "evaluation" / "golden_results.json"


def evaluate_judge() -> dict[str, float | int]:
    if not RESULTS_PATH.is_file():
        raise FileNotFoundError(
            "Run `python src/evaluate_golden_set.py` before evaluating judge labels."
        )
    report = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    results_by_id = {
        result["id"]: result for result in report["results"]
    }
    predictions = {
        case_id: result["judge"]["verdict"]
        for case_id, result in results_by_id.items()
    }
    with LABELS_PATH.open(newline="", encoding="utf-8") as labels_file:
        reader = csv.DictReader(labels_file)
        required_columns = {"id", "draft", "human_verdict", "reason"}
        if set(reader.fieldnames or ()) != required_columns:
            raise ValueError(
                f"Labels CSV must have columns: {', '.join(sorted(required_columns))}."
            )
        labels = list(reader)
    if not labels:
        raise ValueError(
            "No human labels found. Review the generated drafts and fill "
            "evaluation/draft_labels.csv with PASS or FAIL labels."
        )
    if len(labels) < 20:
        raise ValueError("Hand-label at least 20 drafts before reporting judge metrics.")

    seen = set()
    true_positive = false_negative = 0
    true_negative = false_positive = 0
    for label in labels:
        case_id = label["id"]
        human_verdict = label["human_verdict"].strip().upper()
        if case_id in seen or case_id not in predictions:
            raise ValueError(f"Duplicate or unknown case ID in labels: {case_id}")
        if human_verdict not in {"PASS", "FAIL"}:
            raise ValueError(f"Human verdict for {case_id} must be PASS or FAIL.")
        if not label["draft"].strip() or not label["reason"].strip():
            raise ValueError(f"Draft and reason are required for human label {case_id}.")
        if label["draft"].strip() != results_by_id[case_id]["formatted_answer"]:
            raise ValueError(f"Draft for {case_id} does not match the evaluation trace.")
        seen.add(case_id)
        judge_passed = predictions[case_id] == "PASS"
        if human_verdict == "PASS":
            true_positive += judge_passed
            false_negative += not judge_passed
        else:
            true_negative += predictions[case_id] == "FAIL"
            false_positive += predictions[case_id] != "FAIL"

    positive_total = true_positive + false_negative
    negative_total = true_negative + false_positive
    if not positive_total or not negative_total:
        raise ValueError("Human labels must include at least one PASS and one FAIL.")
    report = {
        "labeled_cases": len(labels),
        "true_positive_rate": true_positive / positive_total,
        "true_negative_rate": true_negative / negative_total,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    evaluate_judge()
