from datetime import UTC, datetime
from pathlib import Path

import pytest

from redstone.core.memory import Memory, MemoryType
from redstone.retrieval.semantic import (
    DeterministicEmbeddingProvider,
    EmbeddingCache,
    OpenAIEmbeddingProvider,
    SemanticRetriever,
)


def memory(identifier: str, content: str, *, superseded: str | None = None) -> Memory:
    now = datetime.now(UTC)
    return Memory(
        id=f"memory-{identifier}",
        type=MemoryType.DECISION,
        content=content,
        summary=content,
        source=identifier,
        project="atlas",
        created_at=now,
        updated_at=now,
        observed_at=now,
        superseded_by=superseded,
    )


def test_deterministic_embeddings_and_cache_reuse(tmp_path: Path) -> None:
    provider, cache = DeterministicEmbeddingProvider(), EmbeddingCache(tmp_path / "embeddings.db")
    item = memory("one", "Atlas migrated to SQLite because offline operation was required.")
    retriever = SemanticRetriever(provider, cache)
    assert retriever.search("Why was SQLite selected for Atlas?", [item], project="atlas")
    assert cache.get(item, provider) is not None
    changed = item.model_copy(update={"content": "Atlas migrated to DuckDB."})
    assert cache.get(changed, provider) is None


def test_semantic_retrieval_preserves_current_temporal_filter(tmp_path: Path) -> None:
    cache = EmbeddingCache(tmp_path / "embeddings.db")
    old = memory("old", "Atlas originally chose PostgreSQL.", superseded="memory-new")
    current = memory("new", "Atlas currently uses SQLite.")
    results = SemanticRetriever(DeterministicEmbeddingProvider(), cache).search(
        "What does Atlas use now?", [old, current], project="atlas"
    )
    assert [item.memory.id for item in results] == ["memory-new"]


def test_openai_embedding_requires_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("REDSTONE_EMBEDDING_MODEL", raising=False)
    with pytest.raises(ValueError, match="REDSTONE_EMBEDDING_MODEL"):
        OpenAIEmbeddingProvider.from_environment()
