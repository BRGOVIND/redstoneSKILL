from pathlib import Path

import pytest

from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.storage.filesystem import FilesystemMemoryStore
from redstone.storage.sqlite import SQLiteMemoryStore


@pytest.fixture
def manager(tmp_path: Path) -> MemoryManager:
    return MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))


def test_remember_persists_and_deduplicates(manager: MemoryManager) -> None:
    first, created = manager.remember(
        "Redstone uses SQLite locally.", MemoryType.SEMANTIC, project="redstone"
    )
    second, duplicate_created = manager.remember(
        "  Redstone uses SQLite locally. ", MemoryType.SEMANTIC, project="redstone"
    )
    assert created is True
    assert duplicate_created is False
    assert first.id == second.id
    assert manager.store.get(first.id) == first


def test_search_is_scoped_and_explainable(manager: MemoryManager) -> None:
    manager.remember(
        "Use SQLite for the Redstone metadata store.", project="redstone", importance=0.9
    )
    manager.remember("Use PostgreSQL for billing analytics.", project="billing")
    results = manager.search("SQLite metadata", project="redstone")
    assert len(results) == 1
    assert "keyword match" in results[0].reason
    assert "untrusted data" in manager.recall("SQLite", project="redstone")


def test_secrets_are_not_persisted(manager: MemoryManager) -> None:
    with pytest.raises(ValueError, match="privacy"):
        manager.remember("password=unacceptablylongsecret")
    assert manager.stats()["total"] == 0


def test_recall_tracks_access_and_archive_preserves_record(manager: MemoryManager) -> None:
    memory, _ = manager.remember("Redstone keeps historical truth.")
    manager.recall("historical truth")
    assert manager.store.get(memory.id).access_count == 1
    assert manager.archive(memory.id).status.value == "archived"
    assert manager.store.get(memory.id).status.value == "archived"


def test_filesystem_store_obeys_same_memory_contract(tmp_path: Path) -> None:
    manager = MemoryManager(FilesystemMemoryStore(tmp_path / "memories"))
    memory, created = manager.remember("Portable files remain inspectable.")
    assert created is True
    assert manager.store.get(memory.id) == memory
    assert manager.archive(memory.id).status.value == "archived"
