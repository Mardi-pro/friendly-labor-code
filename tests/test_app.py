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

    def test_non_portuguese_query_is_retrieved_in_portuguese_and_translated_back(self):
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
        query_translation = {
            "portuguese_question": "A empresa pode exigir um teste de gravidez?",
            "portuguese_keywords": "teste gravidez candidata emprego",
        }
        answer_translation = {
            "translation": "No. The employer cannot require that test.\n\n"
            "Legal basis: Article 12.º."
        }
        with (
            patch("app.load_labor_code", return_value=snapshot),
            patch("app.retrieve_articles", return_value=[article]) as retrieve,
            patch(
                "app.ask",
                side_effect=[
                    json.dumps(query_translation),
                    json.dumps(model_result),
                    json.dumps(answer_translation),
                ],
            ) as ask,
        ):
            from app import answer_question

            answer = answer_question("Can an employer require a pregnancy test?")

        self.assertEqual(
            answer,
            "No. The employer cannot require that test.\n\n"
            "Legal basis: Article 12.º.",
        )
        self.assertEqual(
            ask.call_args_list[0].args,
            ("Can an employer require a pregnancy test?",),
        )
        self.assertEqual(
            ask.call_args_list[1].args,
            ("A empresa pode exigir um teste de gravidez?",),
        )
        self.assertEqual(
            ask.call_args_list[2].args,
            (
                json.dumps(
                    {
                        "original_question": "Can an employer require a pregnancy test?",
                        "text": "Resposta\n\nBase legal: Artigo 12.º.",
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        retrieve.assert_called_once_with(
            "teste gravidez candidata emprego", snapshot["articles"]
        )
        self.assertIn(
            "Determine the target language from original_question",
            ask.call_args_list[2].kwargs["system"],
        )
        self.assertIn(
            "12.º — Presunção de contrato de trabalho",
            ask.call_args_list[1].kwargs["system"],
        )
        self.assertIn("Texto do artigo.", ask.call_args_list[1].kwargs["system"])
        self.assertIn(
            "Portuguese Labour Code Q&A — v4",
            ask.call_args_list[1].kwargs["system"],
        )
        normalized_prompt = " ".join(ask.call_args_list[1].kwargs["system"].split())
        self.assertIn(
            "Write the answer and any follow-up question in Portuguese.",
            normalized_prompt,
        )

    def test_portuguese_question_is_used_as_final_translation_target(self):
        snapshot = {
            "source_name": "Portuguese Labor Code",
            "source_url": "https://example.test/source",
            "fetched_at": "2026-10-13T00:00:00+00:00",
            "articles": [],
        }
        article = {"number": "12.º", "title": "Teste", "text": "Texto do artigo."}
        with (
            patch("app.load_labor_code", return_value=snapshot),
            patch("app.retrieve_articles", return_value=[article]),
            patch(
                "app.ask",
                side_effect=[
                    json.dumps(
                        {
                            "portuguese_question": "Pergunta?",
                            "portuguese_keywords": "pergunta",
                        }
                    ),
                    json.dumps(
                        {
                            "status": "answered",
                            "answer": "Resposta",
                            "citations": ["12.º"],
                            "follow_up": None,
                        }
                    ),
                    json.dumps(
                        {"translation": "Resposta\n\nBase legal: Artigo 12.º."}
                    ),
                ],
            ) as ask,
        ):
            from app import answer_question

            answer = answer_question("Pergunta?")

        self.assertEqual(answer, "Resposta\n\nBase legal: Artigo 12.º.")
        self.assertEqual(ask.call_count, 3)
        self.assertIn(
            "If the original question is in Portuguese",
            ask.call_args_list[2].kwargs["system"],
        )

    def test_format_answer_translates_displayed_sources_and_preserves_article_number(self):
        result = {
            "status": "answered",
            "answer": "O empregador não pode exigir o teste.",
            "citations": ["19.º"],
            "follow_up": None,
        }
        articles = [
            {
                "number": "19.º",
                "title": "Testes e exames médicos",
                "text": "O empregador não pode exigir exames de gravidez.",
            }
        ]
        translated = {
            "translation": "The employer cannot require the test.\n\n"
            "Legal basis: Article 19.º.",
            "sources": [
                {
                    "number": "19.º",
                    "title": "Medical tests and examinations",
                    "text": "The employer may not require pregnancy tests.",
                }
            ],
        }
        with patch("app.ask", return_value=json.dumps(translated)) as ask:
            from app import format_answer_with_sources

            answer, sources = format_answer_with_sources(
                result,
                articles,
                "Can an employer require a pregnancy test?",
                "en",
            )

        self.assertEqual(answer, translated["translation"])
        self.assertEqual(sources[0]["number"], "19.º")
        self.assertEqual(sources[0]["title"], "Medical tests and examinations")
        self.assertEqual(
            json.loads(ask.call_args.args[0])["sources"],
            articles,
        )

    def test_format_answer_rejects_changed_source_article_number(self):
        result = {
            "status": "answered",
            "answer": "Resposta",
            "citations": ["19.º"],
            "follow_up": None,
        }
        articles = [
            {"number": "19.º", "title": "Testes", "text": "Texto legal."}
        ]
        response = {
            "translation": "Answer",
            "sources": [
                {"number": "99.º", "title": "Tests", "text": "Legal text."}
            ],
        }
        with (
            patch("app.ask", return_value=json.dumps(response)),
            self.assertRaisesRegex(ValueError, "invalid translated legal source"),
        ):
            from app import format_answer_with_sources

            format_answer_with_sources(
                result,
                articles,
                "Can the employer do this?",
                "en",
            )

    def test_portuguese_interface_returns_portuguese_answer_and_sources_without_translation(self):
        result = {
            "status": "answered",
            "answer": "O empregador não pode exigir o teste.",
            "citations": ["19.º"],
            "follow_up": None,
        }
        articles = [
            {
                "number": "19.º",
                "title": "Testes e exames médicos",
                "text": "O empregador não pode exigir exames de gravidez.",
            }
        ]
        with patch("app.ask") as ask:
            from app import format_answer_with_sources

            answer, sources = format_answer_with_sources(
                result,
                articles,
                "A empresa pode exigir um teste?",
                "pt",
            )

        self.assertEqual(
            answer,
            "O empregador não pode exigir o teste.\n\nBase legal: Artigo 19.º.",
        )
        self.assertEqual(sources, articles)
        ask.assert_not_called()

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
