"""Answer questions with retrieved Portuguese Labour Code articles."""

import json
import sys
from pathlib import Path

from llm import ask
from labor_code import load_labor_code, retrieve_articles

ROOT = Path(__file__).resolve().parents[1]
PROMPT_VERSION = "labor_code_v1"
PROMPT_PATH = ROOT / "prompts" / f"{PROMPT_VERSION}.md"


def _system_prompt(snapshot: dict, articles: list[dict[str, str]]) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    passages = "\n\n".join(
        f"{article['number']} — {article['title']}\n{article['text']}"
        for article in articles
    )
    return (
        f"{prompt}\n\n"
        "Source metadata for this answer:\n"
        f"Source: {snapshot['source_name']}\n"
        f"Source URL: {snapshot['source_url']}\n"
        f"Source snapshot fetched: {snapshot['fetched_at']}\n\n"
        "Retrieved excerpts (the only legal source you may rely on):\n"
        f"{passages or '(No relevant articles retrieved.)'}\n\n"
        "Return the required JSON object only."
    )


def parse_answer(raw: str, articles: list[dict[str, str]]) -> dict[str, object]:
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("The model response was not valid JSON.") from error
    if not isinstance(result, dict) or set(result) != {
        "status", "answer", "citations", "follow_up"
    }:
        raise ValueError("The model response did not match the required answer schema.")
    status = result["status"]
    if not isinstance(status, str) or status not in {"answered", "unknown"}:
        raise ValueError("The model returned an unsupported answer status.")
    if not isinstance(result["answer"], str) or not result["answer"].strip():
        raise ValueError("The model returned an empty answer.")
    citations = result["citations"]
    if not isinstance(citations, list) or any(
        not isinstance(citation, str) for citation in citations
    ):
        raise ValueError("The model returned an invalid citations list.")
    allowed_citations = {article["number"] for article in articles}
    if len(set(citations)) != len(citations) or not set(citations) <= allowed_citations:
        raise ValueError("The model cited an article that was not retrieved.")
    follow_up = result["follow_up"]
    if isinstance(follow_up, str) and not follow_up.strip():
        result["follow_up"] = None
    elif follow_up is not None and not isinstance(follow_up, str):
        raise ValueError("The model returned an invalid follow-up question.")
    if result["status"] == "unknown" and citations:
        raise ValueError("An unknown answer must not cite unsupported articles.")
    if result["status"] == "answered" and not citations:
        raise ValueError("An answered response must cite at least one retrieved article.")
    return result


def analyze_question(question: str) -> tuple[dict[str, object], list[dict[str, str]]]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    snapshot = load_labor_code()
    articles = retrieve_articles(question, snapshot["articles"])
    result = parse_answer(ask(question, system=_system_prompt(snapshot, articles)), articles)
    return result, articles


def format_answer(result: dict[str, object]) -> str:
    answer = str(result["answer"])
    citations = result["citations"]
    if citations:
        references = ", ".join(f"Artigo {citation}" for citation in citations)
        answer = f"{answer}\n\nBase legal: {references}."
    follow_up = result["follow_up"]
    if follow_up:
        answer = f"{answer}\n\nPergunta de seguimento: {follow_up}"
    return answer


def answer_question(question: str) -> str:
    result, _ = analyze_question(question)
    return format_answer(result)


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        raise SystemExit('Usage: python src/app.py "Your labor-law question"')
    question = " ".join(args).strip()
    if not question:
        raise SystemExit("Question cannot be empty.")
    print(answer_question(question))


if __name__ == "__main__":
    main()
