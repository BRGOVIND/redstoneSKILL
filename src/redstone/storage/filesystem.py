"""Portable JSON filesystem store for inspection and export workflows."""

from __future__ import annotations

from pathlib import Path

from redstone.core.memory import Memory, MemoryStatus, utc_now


class FilesystemMemoryStore:
    """Stores one typed JSON document per memory inside a bounded directory."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, memory_id: str) -> Path:
        if not memory_id or Path(memory_id).name != memory_id:
            raise ValueError("invalid memory id")
        return self.root / f"{memory_id}.json"

    def save(self, memory: Memory) -> None:
        path = self._path(memory.id)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(memory.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)

    def get(self, memory_id: str) -> Memory | None:
        path = self._path(memory_id)
        return (
            Memory.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None
        )

    def list(self, *, project: str | None = None, include_archived: bool = False) -> list[Memory]:
        memories = [
            Memory.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.root.glob("*.json")
        ]
        return [
            memory
            for memory in sorted(memories, key=lambda item: item.id)
            if (project is None or memory.project == project)
            and (include_archived or memory.status == MemoryStatus.ACTIVE)
        ]

    def archive(self, memory_id: str) -> Memory:
        memory = self.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        archived = memory.model_copy(
            update={"status": MemoryStatus.ARCHIVED, "updated_at": utc_now()}
        )
        self.save(archived)
        return archived

    def touch(self, memory_id: str) -> Memory:
        memory = self.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        touched = memory.model_copy(
            update={"access_count": memory.access_count + 1, "last_accessed_at": utc_now()}
        )
        self.save(touched)
        return touched
