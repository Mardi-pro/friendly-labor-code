import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import llm


class LlmTests(unittest.TestCase):
    def test_get_client_uses_default_base_url(self):
        with (
            patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=True),
            patch("llm.OpenAI") as openai,
        ):
            client = llm.get_client()

        openai.assert_called_once_with(
            base_url=llm.DEFAULT_BASE_URL, api_key="test-key"
        )
        self.assertIs(client, openai.return_value)

    def test_get_client_uses_configured_base_url(self):
        with (
            patch.dict(
                os.environ,
                {"LLM_API_KEY": "test-key", "LLM_BASE_URL": "https://example.test/v1"},
                clear=True,
            ),
            patch("llm.OpenAI") as openai,
        ):
            llm.get_client()

        openai.assert_called_once_with(
            base_url="https://example.test/v1", api_key="test-key"
        )

    def test_get_client_requires_api_key(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("llm.OpenAI") as openai,
            self.assertRaisesRegex(RuntimeError, "LLM_API_KEY not set"),
        ):
            llm.get_client()

        openai.assert_not_called()

    def test_ask_sends_system_and_user_messages_with_configured_model(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]
        )
        with (
            patch.dict(os.environ, {"LLM_MODEL": "test-model"}, clear=True),
            patch("llm.get_client", return_value=client),
        ):
            answer = llm.ask("question", system="instructions")

        self.assertEqual(answer, "answer")
        client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "instructions"},
                {"role": "user", "content": "question"},
            ],
        )

    def test_ask_omits_empty_system_prompt_and_uses_default_model(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]
        )
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("llm.get_client", return_value=client),
        ):
            answer = llm.ask("question", system="")

        self.assertEqual(answer, "answer")
        client.chat.completions.create.assert_called_once_with(
            model=llm.DEFAULT_MODEL,
            messages=[{"role": "user", "content": "question"}],
        )

    def test_ask_rejects_an_empty_model_response(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )
        with patch("llm.get_client", return_value=client):
            with self.assertRaisesRegex(RuntimeError, "empty response"):
                llm.ask("question")


if __name__ == "__main__":
    unittest.main()
