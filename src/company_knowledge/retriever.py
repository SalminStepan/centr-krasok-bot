from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)
STOPWORDS = {
    "и",
    "в",
    "во",
    "на",
    "по",
    "о",
    "об",
    "а",
    "что",
    "это",
    "как",
    "какие",
    "какая",
    "какой",
    "где",
    "есть",
    "для",
    "с",
    "со",
    "у",
    "ли",
    "the",
    "is",
    "are",
}


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    title: str
    tags: list[str]
    source_urls: list[str]
    text: str


@dataclass(frozen=True)
class SearchResult:
    chunk: KnowledgeChunk
    score: float


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS]


class KnowledgeRetriever:
    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        self.chunks = chunks
        self._chunk_terms = [
            tokenize(" ".join([chunk.title, " ".join(chunk.tags), chunk.text])) for chunk in chunks
        ]
        self._idf = self._build_idf()

    @classmethod
    def from_json(cls, path: Path) -> "KnowledgeRetriever":
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = [KnowledgeChunk(**item) for item in data]
        return cls(chunks)

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        query_set = set(query_terms)
        results: list[SearchResult] = []
        for chunk, terms in zip(self.chunks, self._chunk_terms):
            term_counts = Counter(terms)
            score = 0.0
            for term in query_set:
                if term in term_counts:
                    score += (1 + math.log(term_counts[term])) * self._idf.get(term, 1.0)
            if score:
                score += self._phrase_bonus(query, chunk)
                results.append(SearchResult(chunk=chunk, score=score))

        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]

    def _build_idf(self) -> dict[str, float]:
        docs_count = max(len(self._chunk_terms), 1)
        terms = {term for doc in self._chunk_terms for term in set(doc)}
        idf: dict[str, float] = {}
        for term in terms:
            containing = sum(1 for doc in self._chunk_terms if term in doc)
            idf[term] = math.log((docs_count + 1) / (containing + 1)) + 1
        return idf

    @staticmethod
    def _phrase_bonus(query: str, chunk: KnowledgeChunk) -> float:
        value = query.lower()
        haystack = " ".join([chunk.title, " ".join(chunk.tags), chunk.text]).lower()
        bonus = 0.0
        phrases = (
            "ваканс",
            "адрес",
            "контакт",
            "дизайн",
            "строител",
            "соцсет",
            "instagram",
            "технолог",
            "колеров",
        )
        for phrase in phrases:
            if phrase in value and phrase in haystack:
                bonus += 2.0
        if ("технолог" in value or "колеров" in value) and chunk.id == "tinting_technology":
            bonus += 3.0
        if chunk.id == "faq":
            bonus -= 2.0
        return bonus
