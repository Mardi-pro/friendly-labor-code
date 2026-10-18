"""Run deterministic and LLM-judge checks against the live golden set."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app import PROMPT_VERSION, analyze_question, format_answer
from llm import ask
from labor_code import load_labor_code

GOLDEN_SET_PATH = ROOT / "evaluation" / "golden_set.json"
JUDGE_PROMPT_PATH = ROOT / "evaluation" / "judge_prompt.md"
RESULTS_PATH = ROOT / "evaluation" / "golden_results.json"


def _article_key(reference: str) -> str:
    return reference.removeprefix("Artigo ").strip().casefold()


def _judge_answer(
    question: str, answer: str, articles: list[dict[str, str]]
) -> dict[str, str]:
    prompt = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    evidence = "\n\n".join(
        f"Artigo {article['number']} — {article['title']}\n{article['text']}"
        for article in articles
    )
    raw = ask(
        (
            f"{prompt}\n\nQuestion:\n{question}\n\nDraft:\n{answer}\n\n"
            f"Supplied legal excerpts:\n{evidence or '(No excerpts retrieved.)'}"
        )
    )
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "evidence_quote": "Judge response was not valid JSON.",
            "verdict": "UNKNOWN",
            "validation_error": "invalid_json",
        }
    verdict = result.get("verdict") if isinstance(result, dict) else None
    evidence_quote = result.get("evidence_quote") if isinstance(result, dict) else None
    if (
        not isinstance(result, dict)
        or list(result) != ["evidence_quote", "verdict"]
        or not isinstance(verdict, str)
        or verdict not in {"PASS", "FAIL", "UNKNOWN"}
        or not isinstance(evidence_quote, str)
        or not evidence_quote.strip()
    ):
        return {
            "evidence_quote": "Judge response did not match the required schema.",
            "verdict": "UNKNOWN",
            "validation_error": "invalid_schema",
        }
    if verdict != "UNKNOWN" and not (
        evidence_quote in answer or evidence_quote in evidence
    ):
        return {
            "evidence_quote": "Judge evidence was not an exact quote from the answer or source.",
            "verdict": "UNKNOWN",
            "validation_error": "evidence_not_found",
        }
    return result


def _save_report(snapshot: dict, results: list[dict], total: int) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "prompt_version": PROMPT_VERSION,
                "source_url": snapshot["source_url"],
                "source_fetched_at": snapshot["fetched_at"],
                "results": results,
                "deterministic_passed": sum(
                    result["deterministic_pass"] for result in results
                ),
                "judge_verdicts": {
                    verdict: sum(
                        result["judge"]["verdict"] == verdict for result in results
                    )
                    for verdict in ("PASS", "FAIL", "UNKNOWN")
                },
                "total": total,
                "answered": len(results),
                "completed": sum(
                    result["judge"]["verdict"] != "PENDING" for result in results
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _load_existing_results(snapshot: dict, cases: list[dict]) -> dict[str, dict]:
    if not RESULTS_PATH.is_file():
        return {}
    report = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    if (
        report.get("prompt_version") != PROMPT_VERSION
        or report.get("source_url") != snapshot["source_url"]
        or report.get("source_fetched_at") != snapshot["fetched_at"]
    ):
        raise ValueError(
            "Existing evaluation report uses a different prompt or source snapshot. "
            "Move the report aside before starting a new evaluation."
        )
    expected_cases = {case["id"]: case for case in cases}
    results = {}
    for result in report.get("results", []):
        case_id = result.get("id")
        if case_id not in expected_cases or case_id in results:
            raise ValueError(f"Existing evaluation report has an invalid case ID: {case_id}")
        if result.get("input") != expected_cases[case_id]["input"]:
            raise ValueError(f"Existing evaluation input changed for {case_id}.")
        results[case_id] = result
    return results


def evaluate() -> list[dict]:
    snapshot = load_labor_code()
    cases = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    if len(cases) < 20:
        raise ValueError("The golden set must contain at least 20 cases.")
    results_by_id = _load_existing_results(snapshot, cases)
    for case in cases:
        result = results_by_id.get(case["id"])
        if result and result["judge"]["verdict"] != "PENDING":
            continue
        if result is None:
            answer_started = time.perf_counter()
            structured_answer, retrieved = analyze_question(case["input"])
            answer_latency_ms = round((time.perf_counter() - answer_started) * 1000, 2)
            retrieved_numbers = {
                _article_key(article["number"]) for article in retrieved
            }
            expected_numbers = {
                _article_key(reference) for reference in case["must_retrieve"]
            }
            missing_retrieval = sorted(expected_numbers - retrieved_numbers)
            cited_numbers = {
                _article_key(citation) for citation in structured_answer["citations"]
            }
            missing_citations = sorted(expected_numbers - cited_numbers)
            abstained = structured_answer["status"] == "unknown"
            deterministic_pass = (
                not missing_retrieval
                and not missing_citations
                and abstained == case["should_abstain"]
            )
            formatted_answer = format_answer(structured_answer, case["input"])
            result = {
                "id": case["id"],
                "category": case["category"],
                "input": case["input"],
                "prompt_version": PROMPT_VERSION,
                "answer": structured_answer,
                "formatted_answer": formatted_answer,
                "expected_key_info": case["expected_key_info"],
                "expected_abstention": case["should_abstain"],
                "abstained": abstained,
                "retrieved": sorted(retrieved_numbers),
                "missing_retrieval": missing_retrieval,
                "missing_citations": missing_citations,
                "deterministic_pass": deterministic_pass,
                "judge": {
                    "verdict": "PENDING",
                    "evidence_quote": "Judge request has not completed.",
                },
                "source_fetched_at": snapshot["fetched_at"],
                "answer_latency_ms": answer_latency_ms,
                "judge_latency_ms": None,
            }
            results_by_id[case["id"]] = result
            _save_report(snapshot, list(results_by_id.values()), len(cases))
        else:
            retrieved_by_number = {
                _article_key(article["number"]): article
                for article in snapshot["articles"]
            }
            retrieved = [
                retrieved_by_number[number]
                for number in result["retrieved"]
                if number in retrieved_by_number
            ]
            if len(retrieved) != len(result["retrieved"]):
                raise ValueError(
                    f"Could not restore retrieved source articles for {case['id']}."
                )
            formatted_answer = result["formatted_answer"]

        judge_started = time.perf_counter()
        judgment = _judge_answer(case["input"], formatted_answer, retrieved)
        result["judge"] = judgment
        result["judge_latency_ms"] = round(
            (time.perf_counter() - judge_started) * 1000, 2
        )
        results = list(results_by_id.values())
        _save_report(snapshot, results, len(cases))
        status = "PASS" if result["deterministic_pass"] else "FAIL"
        print(f"{status} {case['id']} — {case['category']}")
        if result["missing_retrieval"]:
            print(f"  Missing from retrieval: {', '.join(result['missing_retrieval'])}")
        if result["missing_citations"]:
            print(f"  Missing citations: {', '.join(result['missing_citations'])}")
        if case["should_abstain"] != result["abstained"]:
            print(
                f"  Abstention expected={case['should_abstain']}, "
                f"got={result['abstained']}"
            )
        print(f"  Answer: {formatted_answer.replace(chr(10), ' ')}")
        print(f"  Judge: {judgment['verdict']} — {judgment['evidence_quote']}")
        if "validation_error" in judgment:
            print(f"  Judge validation issue: {judgment['validation_error']}")
    results = [results_by_id[case["id"]] for case in cases]
    _save_report(snapshot, results, len(cases))
    passed = sum(result["deterministic_pass"] for result in results)
    print(f"\nDeterministic checks: {passed}/{len(results)} passed.")
    judge_counts = {
        verdict: sum(result["judge"]["verdict"] == verdict for result in results)
        for verdict in ("PASS", "FAIL", "UNKNOWN")
    }
    print(f"Judge verdicts: {json.dumps(judge_counts)}")
    print(f"Detailed report: {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    evaluate()
