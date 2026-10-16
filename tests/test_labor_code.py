import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import labor_code


class LaborCodeTests(unittest.TestCase):
    def test_extracts_article_headers_and_text(self):
        html = """
        <html><head><title>Lei de teste</title></head><body>
          <table class="artigo"><tr><td>SECÇÃO I Artigo 12.º-A Presunção laboral</td></tr></table>
          <table><tr><td>1 - Texto legal &amp; esclarecimento.<br>2 - Segundo número.</td></tr></table>
          <table class="artigo"><tr><td>Artigo 13.º Outro artigo</td></tr></table>
          <table><tr><td>Regra aplicável.</td></tr></table>
        </body></html>
        """

        title, articles = labor_code._extract_page_articles(html)

        self.assertEqual(title, "Lei de teste")
        self.assertEqual(
            articles,
            [
                {
                    "number": "12.º-A",
                    "title": "Presunção laboral",
                    "text": "1 - Texto legal & esclarecimento.\n2 - Segundo número.",
                },
                {
                    "number": "13.º",
                    "title": "Outro artigo",
                    "text": "Regra aplicável.",
                },
            ],
        )

    def test_discovers_only_law_pages_for_configured_source(self):
        html = """
        <a href="lei_mostra_articulado.php?ficha=101&nid=1047&pagina=2&tabela=leis">2</a>
        <a href="https://evil.example/lei_mostra_articulado.php?ficha=201&amp;nid=1047&amp;tabela=leis">bad</a>
        <a href="lei_mostra_articulado.php?ficha=1&nid=1047&tabela=lei_velhas">old</a>
        """

        urls = labor_code._page_urls(html)

        self.assertEqual(len(urls), 2)
        self.assertIn("ficha=1", urls[0])
        self.assertIn("ficha=101", urls[1])
        self.assertTrue(all("www.pgdlisboa.pt" in url for url in urls))

    def test_retriever_prefers_matching_article_title_and_text(self):
        articles = [
            {
                "number": "20.º",
                "title": "Meios de vigilância a distância",
                "text": "Não pode controlar o desempenho profissional através de vigilância.",
            },
            {
                "number": "47.º",
                "title": "Dispensa para amamentação",
                "text": "A trabalhadora tem direito a dispensa diária para amamentar.",
            },
            {
                "number": "140.º",
                "title": "Contrato a termo resolutivo",
                "text": "Necessidades temporárias da empresa.",
            },
        ]

        results = labor_code.retrieve_articles(
            "O empregador pode usar vigilância para controlar o desempenho?", articles
        )

        self.assertEqual(results[0]["number"], "20.º")

    def test_retriever_adds_definition_with_a_relevant_contract_presumption(self):
        articles = [
            {
                "number": "11.º",
                "title": "Noção de contrato de trabalho",
                "text": "Define o contrato de trabalho.",
            },
            {
                "number": "12.º",
                "title": "Presunção de contrato de trabalho",
                "text": "Presume-se a existência de contrato.",
            },
            {
                "number": "140.º",
                "title": "Contrato a termo resolutivo",
                "text": "Necessidades temporárias da empresa.",
            },
        ]

        results = labor_code.retrieve_articles(
            "Pode exigir o reconhecimento de contrato de trabalho?", articles
        )

        self.assertIn("12.º", {article["number"] for article in results})
        self.assertIn("11.º", {article["number"] for article in results})

    def test_retriever_returns_no_articles_for_empty_or_unrelated_terms(self):
        articles = [
            {
                "number": "47.º",
                "title": "Dispensa para amamentação",
                "text": "A trabalhadora tem direito a dispensa diária.",
            }
        ]

        self.assertEqual(labor_code.retrieve_articles("???", articles), [])
        self.assertEqual(
            labor_code.retrieve_articles("astronomia galáxia", articles), []
        )

    def test_missing_cache_explains_how_to_create_it(self):
        with self.assertRaisesRegex(FileNotFoundError, "python src/fetch_law.py"):
            labor_code.load_labor_code(Path("/path/that/does/not/exist.json"))


if __name__ == "__main__":
    unittest.main()
