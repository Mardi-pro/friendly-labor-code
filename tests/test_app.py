import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class AppTests(unittest.TestCase):
    def run_app(self, argv):
        output = io.StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch("app.answer_question", return_value="mock response") as answer,
            redirect_stdout(output),
        ):
            from app import main

            main()
        return answer, output.getvalue()

    def test_joins_command_line_arguments_into_prompt(self):
        answer, output = self.run_app(["app.py", "Explain", "Article 12"])

        answer.assert_called_once_with("Explain Article 12")
        self.assertEqual(output, "mock response\n")

    def test_requires_a_question(self):
        with self.assertRaisesRegex(SystemExit, "Usage:"):
            self.run_app(["app.py"])
        with self.assertRaisesRegex(SystemExit, "cannot be empty"):
            self.run_app(["app.py", "  "])

    def test_answer_question_includes_retrieved_source_in_system_prompt(self):
        snapshot = {
            "source_name": "Portuguese Labor Code",
            "source_url": "https://example.test/source",
            "fetched_at": "2026-10-13T00:00:00+00:00",
            "articles": [],
        }
        article = {
            "number": "12.º",
            "title": "Presunção de contrato de trabalho",
            "text": "Texto do artigo.",
        }
        model_result = {
            "status": "answered",
            "answer": "Resposta",
            "citations": ["12.º"],
            "follow_up": None,
        }
        with (
            patch("app.load_labor_code", return_value=snapshot),
            patch("app.retrieve_articles", return_value=[article]),
            patch("app.ask", return_value=json.dumps(model_result)) as ask,
        ):
            from app import answer_question

            answer = answer_question("Pergunta?")

        self.assertEqual(answer, "Resposta\n\nBase legal: Artigo 12.º.")
        args, kwargs = ask.call_args
        self.assertEqual(args, ("Pergunta?",))
        self.assertIn("12.º — Presunção de contrato de trabalho", kwargs["system"])
        self.assertIn("Texto do artigo.", kwargs["system"])
        self.assertIn("Portuguese Labour Code Q&A — v2", kwargs["system"])
        normalized_prompt = " ".join(kwargs["system"].split())
        self.assertIn(
            "Write the entire response, including `answer` and `follow_up`, in "
            "the same language as the user's question.",
            normalized_prompt,
        )

    def test_no_retrieved_articles_can_only_return_an_uncited_unknown(self):
        from app import parse_answer

        response = {
            "status": "unknown",
            "answer": "Não consigo determinar a resposta pelos excertos fornecidos.",
            "citations": [],
            "follow_up": None,
        }

        self.assertEqual(parse_answer(json.dumps(response), [])["status"], "unknown")

    def test_empty_follow_up_is_normalized_to_null(self):
        from app import parse_answer

        response = {
            "status": "answered",
            "answer": "Resposta",
            "citations": ["12.º"],
            "follow_up": " ",
        }

        result = parse_answer(
            json.dumps(response),
            [{"number": "12.º", "title": "Teste", "text": "Texto"}],
        )
        self.assertIsNone(result["follow_up"])

    def test_rejects_invalid_json_and_unretrieved_citations(self):
        from app import parse_answer

        with self.assertRaisesRegex(ValueError, "valid JSON"):
            parse_answer("not json", [])
        with self.assertRaisesRegex(ValueError, "not retrieved"):
            parse_answer(
                json.dumps(
                    {
                        "status": "answered",
                        "answer": "Resposta",
                        "citations": ["99.º"],
                        "follow_up": None,
                    }
                ),
                [],
            )

    def test_unknown_answer_has_no_citation_and_has_follow_up(self):
        from app import parse_answer

        with self.assertRaisesRegex(ValueError, "must not cite"):
            parse_answer(
                json.dumps(
                    {
                        "status": "unknown",
                        "answer": "Resposta",
                        "citations": ["12.º"],
                        "follow_up": None,
                    }
                ),
                [{"number": "12.º", "title": "Teste", "text": "Texto"}],
            )


if __name__ == "__main__":
    unittest.main()
