#!/usr/bin/env python3
"""Collect raw and cleaned source pages for the company knowledge base."""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_PAGES_DIR = RAW_DIR / "pages"
PROCESSED_DIR = ROOT / "data" / "processed"

SOURCE_URLS = [
    "https://centr-krasok.kz/",
    "https://centr-krasok.kz/about/",
    "https://centr-krasok.kz/about/contacts/",
    "https://centr-krasok.kz/catalog/",
    "https://centr-krasok.kz/brands/",
    "https://centr-krasok.kz/tinting/",
    "https://centr-krasok.kz/partners/",
    "https://centr-krasok.kz/designers/",
    "https://centr-krasok.kz/for_builders/",
    "https://centr-krasok.kz/for_builders_company/",
    "https://centr-krasok.kz/news/",
    "https://centr-krasok.kz/news/tsentr_krasok_1_na_dizaynerskoy_vystavke/",
    "https://centr-krasok.kz/news/tsentr_krasok_1_vybor_strany/",
    "https://centr-krasok.kz/promotions/",
    "https://centr-krasok.kz/about/offer_agreement/",
]


@dataclass
class SourcePage:
    url: str
    title: str
    status: int
    html_file: str
    text_file: str
    fetched_at: str
    sha256: str
    error: str | None = None


class ReadableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if not value:
            return
        if self._in_title:
            self.title = value
        self._chunks.append(value)

    def text(self) -> str:
        raw = " ".join(self._chunks)
        raw = html.unescape(raw)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s+", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        noise_patterns = [
            r"РУС Русский Қазақша English",
            r"Ваш город Алматы\? Да Нет, выбрать другой",
            r"0 0 Корзина Профиль",
        ]
        for pattern in noise_patterns:
            raw = re.sub(pattern, " ", raw)
        return raw.strip()


def slug_for_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "home"
    slug = re.sub(r"[^a-zA-Z0-9а-яА-Я_-]+", "-", path).strip("-").lower()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AICompanyAssistantBot/0.1 (+https://centr-krasok.kz/)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read()


def scrape() -> list[SourcePage]:
    RAW_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pages: list[SourcePage] = []

    for index, url in enumerate(SOURCE_URLS, start=1):
        slug = slug_for_url(url)
        html_path = RAW_PAGES_DIR / f"{index:02d}-{slug}.html"
        text_path = RAW_PAGES_DIR / f"{index:02d}-{slug}.txt"
        fetched_at = datetime.now(timezone.utc).isoformat()
        try:
            status, body = fetch(url)
            html_text = body.decode("utf-8", errors="replace")
            parser = ReadableTextParser()
            parser.feed(html_text)
            clean_text = parser.text()
            html_path.write_text(html_text, encoding="utf-8")
            text_path.write_text(clean_text, encoding="utf-8")
            pages.append(
                SourcePage(
                    url=url,
                    title=parser.title,
                    status=status,
                    html_file=str(html_path.relative_to(ROOT)),
                    text_file=str(text_path.relative_to(ROOT)),
                    fetched_at=fetched_at,
                    sha256=hashlib.sha256(body).hexdigest(),
                )
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            pages.append(
                SourcePage(
                    url=url,
                    title="",
                    status=0,
                    html_file=str(html_path.relative_to(ROOT)),
                    text_file=str(text_path.relative_to(ROOT)),
                    fetched_at=fetched_at,
                    sha256="",
                    error=str(exc),
                )
            )
        time.sleep(0.6)

    manifest_path = RAW_DIR / "sources_manifest.json"
    manifest_path.write_text(
        json.dumps([asdict(page) for page in pages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return pages


if __name__ == "__main__":
    result = scrape()
    ok = sum(1 for item in result if item.status)
    print(f"Saved {ok}/{len(result)} source pages into {RAW_PAGES_DIR}")
