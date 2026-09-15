"""SQLite persistence for typed Redstone memories."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from redstone.core.memory import Memory, MemoryStatus, utc_now


class SQLiteMemoryStore:
    """Small, transactional store with JSON payloads and searchable projections."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, type TEXT NOT NULL, project TEXT,
                    status TEXT NOT NULL, content TEXT NOT NULL, payload TEXT NOT NULL
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS ix_memories_project ON memories(project)"
            )
            connection.execute("CREATE INDEX IF NOT EXISTS ix_memories_status ON memories(status)")

    def save(self, memory: Memory) -> None:
        payload = json.dumps(memory.model_dump(mode="json"), sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO memories(id, type, project, status, content, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET type=excluded.type, project=excluded.project,
                status=excluded.status, content=excluded.content, payload=excluded.payload""",
                (
                    memory.id,
                    memory.type.value,
                    memory.project,
                    memory.status.value,
                    memory.content,
                    payload,
                ),
            )

    def get(self, memory_id: str) -> Memory | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        return Memory.model_validate_json(row["payload"]) if row else None

    def list(self, *, project: str | None = None, include_archived: bool = False) -> list[Memory]:
        clauses: list[str] = []
        params: list[str] = []
        if project:
            clauses.append("project = ?")
            params.append(project)
        if not include_archived:
            clauses.append("status = ?")
            params.append(MemoryStatus.ACTIVE.value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM memories{where} ORDER BY id", params
            ).fetchall()
        return [Memory.model_validate_json(row["payload"]) for row in rows]

    def archive(self, memory_id: str) -> Memory:
        memory = self.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        archived = memory.model_copy(update={"status": MemoryStatus.ARCHIVED})
        self.save(archived)
        return archived

    def touch(self, memory_id: str) -> Memory:
        """Record a retrieval without mutating memory content or provenance."""
        memory = self.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        touched = memory.model_copy(
            update={"access_count": memory.access_count + 1, "last_accessed_at": utc_now()}
        )
        self.save(touched)
        return touched
