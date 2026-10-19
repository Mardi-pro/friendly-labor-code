import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import evaluate_golden_set
import evaluate_judge


class EvaluationTests(unittest.TestCase):
    def test_resume_loads_only_matching_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "golden_results.json"
            snapshot = {
                "source_url": "https://example.test/source",
                "fetched_at": "2026-10-16T00:00:00+00:00",
            }
            cases = [{"id": "CT-001", "input": "Question"}]
            report_path.write_text(
                json.dumps(
                    {
                        "prompt_version": evaluate_golden_set.PROMPT_VERSION,
                        "judge_prompt_version": evaluate_golden_set.JUDGE_PROMPT_VERSION,
                        "source_url": snapshot["source_url"],
                        "source_fetched_at": snapshot["fetched_at"],
                        "results": [{"id": "CT-001", "input": "Question"}],
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(evaluate_golden_set, "RESULTS_PATH", report_path):
                loaded = evaluate_golden_set._load_existing_results(snapshot, cases)
                self.assertIn("CT-001", loaded)
                with self.assertRaisesRegex(ValueError, "different answer prompt"):
                    evaluate_golden_set._load_existing_results(
                        {**snapshot, "fetched_at": "different"}, cases
                    )

    def test_judge_rejects_non_exact_evidence_as_unknown(self):
        article = {"number": "12.º", "title": "Teste", "text": "Trecho legal."}
        with patch("evaluate_golden_set.ask", return_value=json.dumps(
            {"evidence_quote": "Resposta baseada no trecho.", "verdict": "PASS"}
        )):
            result = evaluate_golden_set._judge_answer(
                "Pergunta?", "Resposta baseada no trecho.", [article]
            )
        self.assertEqual(result["verdict"], "PASS")

        with patch("evaluate_golden_set.ask", return_value=json.dumps(
            {"evidence_quote": "texto inventado", "verdict": "PASS"}
        )):
            result = evaluate_golden_set._judge_answer(
                "Pergunta?", "Resposta.", [article]
            )
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["validation_error"], "evidence_not_found")

    def test_judge_receives_original_answer_not_translated_display_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases_path = root / "golden_set.json"
            results_path = root / "golden_results.json"
            cases = [
                {
                    "id": f"CT-{index:03d}",
                    "category": "Test",
                    "input": "Pergunta?",
                    "must_retrieve": [],
                    "expected_key_info": "Test info",
                    "should_abstain": False,
                }
                for index in range(1, 21)
            ]
            cases_path.write_text(json.dumps(cases), encoding="utf-8")
            snapshot = {
                "source_url": "https://example.test/source",
                "fetched_at": "2026-10-16T00:00:00+00:00",
                "articles": [],
            }
            original_answer = {
                "status": "answered",
                "answer": "Resposta original em português.",
                "citations": ["12.º"],
                "follow_up": None,
            }
            with (
                patch.object(evaluate_golden_set, "GOLDEN_SET_PATH", cases_path),
                patch.object(evaluate_golden_set, "RESULTS_PATH", results_path),
                patch.object(evaluate_golden_set, "load_labor_code", return_value=snapshot),
                patch.object(
                    evaluate_golden_set,
                    "analyze_question",
                    return_value=(original_answer, []),
                ),
                patch.object(
                    evaluate_golden_set,
                    "format_answer",
                    return_value="Translated display answer.",
                ),
                patch.object(
                    evaluate_golden_set,
                    "_judge_answer",
                    return_value={"verdict": "UNKNOWN", "evidence_quote": "reason"},
                ) as judge,
            ):
                evaluate_golden_set.evaluate()

        self.assertEqual(
            judge.call_args_list[0].args[1], original_answer["answer"]
        )

    def test_invalid_judge_json_is_recorded_as_unknown(self):
        with patch("evaluate_golden_set.ask", return_value="not json"):
            result = evaluate_golden_set._judge_answer("Pergunta?", "Resposta.", [])
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(result["validation_error"], "invalid_json")

    def test_judge_unknown_exit_is_accepted_with_a_reason(self):
        with patch("evaluate_golden_set.ask", return_value=json.dumps(
            {"evidence_quote": "Informação insuficiente.", "verdict": "UNKNOWN"}
        )):
            result = evaluate_golden_set._judge_answer("Pergunta?", "Resposta.", [])
        self.assertEqual(result["verdict"], "UNKNOWN")

    def test_human_label_metrics_and_unknown_judge_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results_path = root / "golden_results.json"
            labels_path = root / "draft_labels.csv"
            results = []
            label_lines = ["id,draft,human_verdict,reason"]
            for index in range(20):
                case_id = f"CT-{index + 1:03d}"
                if index == 9:
                    judge_verdict = "FAIL"
                elif index == 19:
                    judge_verdict = "UNKNOWN"
                else:
                    judge_verdict = "PASS" if index < 10 else "FAIL"
                human_verdict = "PASS" if index < 10 else "FAIL"
                draft = f"Draft for {case_id}"
                results.append(
                    {
                        "id": case_id,
                        "judge": {"verdict": judge_verdict},
                        "formatted_answer": draft,
                    }
                )
                label_lines.append(
                    f"{case_id},{draft},{human_verdict},Hand reviewed"
                )
            results_path.write_text(
                json.dumps({"results": results}),
                encoding="utf-8",
            )
            labels_path.write_text("\n".join(label_lines) + "\n", encoding="utf-8")
            with (
                patch.object(evaluate_judge, "RESULTS_PATH", results_path),
                patch.object(evaluate_judge, "LABELS_PATH", labels_path),
            ):
                report = evaluate_judge.evaluate_judge()

        self.assertEqual(report["labeled_cases"], 20)
        self.assertEqual(report["true_positive_rate"], 0.9)
        self.assertEqual(report["true_negative_rate"], 0.9)


if __name__ == "__main__":
    unittest.main()
