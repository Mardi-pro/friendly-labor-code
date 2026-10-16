"""Download, cache, and search the Portuguese Labour Code source."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

SOURCE_URL = (
    "https://www.pgdlisboa.pt/leis/lei_mostra_articulado.php"
    "?ficha=1&artigo_id=&nid=1047&pagina=1&tabela=leis&nversao=&so_miolo="
)
SOURCE_NAME = "Lei n.º 7/2009, de 12 de fevereiro (Código do Trabalho)"
SOURCE_BASE = "https://www.pgdlisboa.pt/leis/"
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "labor_code.json"
ARTICLE_PATTERN = re.compile(
    r"\bArtigo\s+(\d+\.º(?:-[A-Z])?)\s*(.*?)$", re.IGNORECASE
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "à", "às", "ao", "aos", "as", "com", "como", "da", "das", "de",
    "do", "dos", "e", "em", "entre", "essa", "esse", "esta", "este", "eu",
    "foi", "for", "há", "isso", "isto", "lhe", "mais", "mas", "me", "na",
    "nas", "nem", "no", "nos", "o", "os", "ou", "para", "pela", "pelas",
    "pelo", "pelos", "por", "qual", "quando", "que", "quem", "se", "sem",
    "ser", "seu", "sua", "suas", "seus", "sobre", "tem", "um", "uma",
    "umas", "uns", "é",
}
QUERY_SYNONYMS = {
    "prestador": {"contrato", "trabalho", "atividade"},
    "candidata": {"candidato", "teste", "gravidez"},
    "camaras": {"vigilancia", "distancia", "local"},
    "camera": {"vigilancia", "distancia", "local"},
    "videovigilancia": {"vigilancia", "distancia", "desempenho"},
    "controlar": {"controlo", "desempenho"},
    "produtividade": {"desempenho"},
    "ganha": {"retribuicao", "igualdade", "discriminacao"},
    "ganhar": {"retribuicao", "igualdade", "discriminacao"},
    "salario": {"retribuicao", "igualdade"},
    "salarios": {"retribuicao", "igualdade"},
    "menos": {"diferenca", "retribuicao"},
    "funcoes": {"trabalho", "igualdade"},
}


def _download(url: str) -> str:
    request = Request(url, headers={"User-Agent": "friendly-labor-code/1.0"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Legal source returned HTTP {response.status}")
        return response.read().decode("iso-8859-1", errors="replace")


def _page_urls(first_html: str) -> list[str]:
    soup = BeautifulSoup(first_html, "html.parser")
    urls = {SOURCE_URL}
    for link in soup.find_all("a", href=True):
        candidate = urljoin(SOURCE_BASE, link["href"])
        parsed = urlparse(candidate)
        params = parse_qs(parsed.query)
        if (
            parsed.netloc == "www.pgdlisboa.pt"
            and parsed.path.endswith("/lei_mostra_articulado.php")
            and params.get("nid") == ["1047"]
            and params.get("tabela") == ["leis"]
            and params.get("ficha", ["1"])[0].isdigit()
        ):
            urls.add(candidate)
    return sorted(
        urls,
        key=lambda candidate: int(
            parse_qs(urlparse(candidate).query).get("ficha", ["1"])[0]
        ),
    )


def _extract_page_articles(html: str) -> tuple[str, list[dict[str, str]]]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else SOURCE_NAME
    articles = []
    for heading in soup.find_all("table", class_="artigo"):
        heading_text = heading.get_text(" ", strip=True)
        match = ARTICLE_PATTERN.search(heading_text)
        body = heading.find_next_sibling("table")
        if not match or body is None:
            continue
        text = unescape(body.get_text("\n", strip=True))
        if not text:
            continue
        articles.append(
            {
                "number": match.group(1),
                "title": match.group(2).strip(),
                "text": text,
            }
        )
    return title, articles


def fetch_labor_code() -> dict:
    first_html = _download(SOURCE_URL)
    pages = []
    source_title = SOURCE_NAME
    for page_url in _page_urls(first_html):
        html = first_html if page_url == SOURCE_URL else _download(page_url)
        title, page_articles = _extract_page_articles(html)
        source_title = title or source_title
        pages.extend(page_articles)

    by_number = {article["number"]: article for article in pages}
    if not by_number:
        raise RuntimeError("No labor-code articles were found at the configured source.")

    return {
        "source_name": SOURCE_NAME,
        "source_title": source_title,
        "source_url": SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "articles": list(by_number.values()),
    }


def save_labor_code(snapshot: dict, path: Path = DATA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_labor_code(path: Path = DATA_PATH) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Labor-code source is not cached at {path}. "
            "Run `python src/fetch_law.py` first."
        )
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(snapshot.get("articles"), list) or not snapshot["articles"]:
        raise ValueError(f"Labor-code source cache is empty or invalid: {path}")
    return snapshot


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in normalized if not unicodedata.combining(char))
    return [
        token for token in TOKEN_PATTERN.findall(plain)
        if len(token) > 2 and token not in STOP_WORDS
    ]


def retrieve_articles(
    question: str, articles: list[dict[str, str]], top_k: int = 10
) -> list[dict[str, str]]:
    query_terms = set(_tokens(question))
    query_terms.update(
        synonym
        for term in tuple(query_terms)
        for synonym in QUERY_SYNONYMS.get(term, set())
    )
    if not query_terms or top_k < 1:
        return []

    documents = [
        (article, set(_tokens(article["title"])), Counter(_tokens(article["text"])))
        for article in articles
    ]
    document_frequency = Counter()
    for _, title_terms, body_terms in documents:
        document_frequency.update(title_terms | body_terms.keys())

    ranked = []
    corpus_size = len(documents)
    for article, title_terms, body_terms in documents:
        score = 0.0
        for term in query_terms:
            frequency = body_terms.get(term, 0)
            if term in title_terms or frequency:
                inverse_frequency = math.log(
                    1 + corpus_size / (1 + document_frequency[term])
                )
                score += inverse_frequency * (
                    (3.0 if term in title_terms else 0.0)
                    + min(frequency, 3) * 0.35
                )
        if score:
            ranked.append((score, article))

    ranked.sort(key=lambda item: (-item[0], item[1]["number"]))
    selected = [article for _, article in ranked[:top_k]]
    selected_numbers = {article["number"] for article in selected}

    if any(
        "presuncao" in _tokens(article["title"])
        and {"contrato", "trabalho"} <= set(_tokens(article["title"]))
        for article in selected
    ):
        definition = next(
            (
                article for article in articles
                if "nocao" in _tokens(article["title"])
                and {"contrato", "trabalho"} <= set(_tokens(article["title"]))
            ),
            None,
        )
        if definition and definition["number"] not in selected_numbers:
            selected.append(definition)

    return selected
