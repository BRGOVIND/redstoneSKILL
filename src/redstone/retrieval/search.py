"""Transparent lexical retrieval used when embeddings are unavailable."""

from __future__ import annotations

import re
from dataclasses import dataclass

from redstone.core.memory import Memory

_WORD = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "user",
    "was",
    "what",
    "when",
    "which",
    "who",
}


@dataclass(frozen=True)
class SearchResult:
    memory: Memory
    score: float
    reason: str


def _terms(text: str) -> set[str]:
    return {term for term in _WORD.findall(text.lower()) if term not in _STOPWORDS}


def keyword_search(query: str, memories: list[Memory], *, limit: int = 10) -> list[SearchResult]:
    """Rank by Jaccard overlap, with deterministic score and tie ordering."""
    query_terms = _terms(query)
    if not query_terms:
        return []
    results: list[SearchResult] = []
    for memory in memories:
        body_terms = _terms(f"{memory.content} {memory.summary} {' '.join(memory.tags)}")
        overlap = query_terms & body_terms
        if not overlap:
            continue
        relevance = len(overlap) / len(query_terms | body_terms)
        score = round(0.7 * relevance + 0.2 * memory.importance + 0.1 * memory.confidence, 6)
        results.append(SearchResult(memory, score, f"keyword match: {', '.join(sorted(overlap))}"))
    return sorted(results, key=lambda item: (-item.score, item.memory.id))[:limit]
