"""Optional local semantic candidate retrieval; no vector service required."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from redstone.core.memory import Memory
from redstone.retrieval.query import QueryIntent, parse_intent
from redstone.retrieval.search import SearchResult, _terms


class EmbeddingProvider(Protocol):
    name: str
    model: str

    def embed(self, text: str) -> tuple[float, ...]:
        """Return deterministic vector for text."""


_SYNONYMS = {
    "selected": "decision",
    "choose": "decision",
    "chose": "decision",
    "migrated": "decision",
    "migration": "decision",
    "why": "reason",
    "because": "reason",
    "drove": "reason",
    "nowadays": "current",
    "currently": "current",
    "preceded": "original",
    "before": "original",
}


@dataclass(frozen=True)
class DeterministicEmbeddingProvider:
    """Hash-vector test embedding with authored synonym normalization."""

    name: str = "deterministic"
    model: str = "deterministic-semantic-v1"
    dimensions: int = 64

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimensions
        for term in _terms(text):
            canonical = _SYNONYMS.get(term, term)
            vector[int(hashlib.sha256(canonical.encode()).hexdigest(), 16) % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return tuple(value / norm for value in vector) if norm else tuple(vector)


@dataclass(frozen=True)
class OpenAIEmbeddingProvider:
    """Optional OpenAI adapter; credentials remain environment-only."""

    api_key: str
    model: str
    name: str = "openai"

    @classmethod
    def from_environment(cls) -> OpenAIEmbeddingProvider:
        key, model = (
            os.getenv("OPENAI_API_KEY", "").strip(),
            os.getenv("REDSTONE_EMBEDDING_MODEL", "").strip(),
        )
        if not key or not model:
            raise ValueError(
                "OpenAI embeddings require OPENAI_API_KEY and REDSTONE_EMBEDDING_MODEL."
            )
        return cls(key, model)

    def embed(self, text: str) -> tuple[float, ...]:
        request = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=json.dumps({"model": self.model, "input": text}).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode())
        return tuple(float(value) for value in body["data"][0]["embedding"])


class EmbeddingCache:
    """Local SQLite cache keyed by memory content hash and provider model."""

    def __init__(self, path: Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS embeddings (memory_id TEXT, content_hash TEXT, provider TEXT, model TEXT, vector TEXT, PRIMARY KEY(memory_id, content_hash, provider, model))"
        )

    def get(self, memory: Memory, provider: EmbeddingProvider) -> tuple[float, ...] | None:
        digest = hashlib.sha256(memory.content.encode()).hexdigest()
        row = self.connection.execute(
            "SELECT vector FROM embeddings WHERE memory_id=? AND content_hash=? AND provider=? AND model=?",
            (memory.id, digest, provider.name, provider.model),
        ).fetchone()
        return tuple(float(value) for value in row[0].split(",")) if row else None

    def put(self, memory: Memory, provider: EmbeddingProvider, vector: tuple[float, ...]) -> None:
        digest = hashlib.sha256(memory.content.encode()).hexdigest()
        self.connection.execute(
            "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?, ?)",
            (memory.id, digest, provider.name, provider.model, ",".join(map(str, vector))),
        )
        self.connection.commit()


@dataclass
class SemanticRetriever:
    provider: EmbeddingProvider
    cache: EmbeddingCache

    def search(
        self, query: str, memories: list[Memory], *, project: str | None = None, limit: int = 20
    ) -> list[SearchResult]:
        query_vector = self.provider.embed(query)
        intent = parse_intent(query)
        results = []
        for memory in memories:
            if project and memory.project != project:
                continue
            if intent == QueryIntent.CURRENT and memory.superseded_by:
                continue
            if intent == QueryIntent.HISTORICAL and not memory.superseded_by:
                continue
            vector = self.cache.get(memory, self.provider)
            if vector is None:
                vector = self.provider.embed(memory.content)
                self.cache.put(memory, self.provider, vector)
            score = sum(left * right for left, right in zip(query_vector, vector))
            if score > 0:
                results.append(SearchResult(memory, round(score, 6), "semantic candidate"))
        return sorted(results, key=lambda item: (-item.score, item.memory.id))[:limit]
