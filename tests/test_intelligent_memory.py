from pathlib import Path

from redstone.core.manager import MemoryManager
from redstone.mcp.server import call_tool
from redstone.storage.sqlite import SQLiteMemoryStore


def test_hybrid_context_timeline_and_related(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    old, _ = manager.remember("Old Redstone decision.", project="redstone", importance=0.1)
    current, _ = manager.remember(
        "Redstone chose SQLite metadata.", project="redstone", importance=0.9
    )
    manager.supersede(old.id, current.id)
    manager.link(current.id, old.id, "derived_from")
    assert "REDSTONE MEMORY CONTEXT" in manager.recall("SQLite metadata", project="redstone")
    assert manager.timeline("redstone")[0].id == old.id
    assert manager.related(old.id)[0].id == current.id


def test_update_and_mcp_tools(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    memory, _ = manager.remember("Initial decision.", project="redstone")
    assert manager.update(memory.id, "Updated decision.").version == 2
    response = call_tool("memory_search", {"query": "Updated", "project": "redstone"}, manager)
    assert response["memories"][0]["id"] == memory.id
    assert call_tool("memory_stats", {}, manager)["active"] == 1
