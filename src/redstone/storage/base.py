"""Storage interface for provider-independent memory persistence."""

from __future__ import annotations

from typing import Protocol

from redstone.core.memory import Memory


class MemoryStore(Protocol):
    """Minimum persistence contract used by the memory engine."""

    def save(self, memory: Memory) -> None: ...

    def get(self, memory_id: str) -> Memory | None: ...

    def list(
        self, *, project: str | None = None, include_archived: bool = False
    ) -> list[Memory]: ...

    def archive(self, memory_id: str) -> Memory: ...

    def touch(self, memory_id: str) -> Memory: ...
