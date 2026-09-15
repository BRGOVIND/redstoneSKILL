"""Non-destructive Obsidian synchronization adapter."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from redstone.core.memory import Memory, MemoryType, utc_now
from redstone.privacy.policy import PrivacyPolicy
from redstone.storage.base import MemoryStore

from .serializer import (
    markdown_to_memory,
    memory_hash,
    memory_to_markdown,
    normalized_hash,
    read_markdown,
    safe_filename,
)

_TYPE_DIRECTORIES = {
    MemoryType.SEMANTIC: "Semantic",
    MemoryType.EPISODIC: "Episodic",
    MemoryType.PROCEDURAL: "Procedural",
    MemoryType.PREFERENCE: "Preferences",
    MemoryType.DECISION: "Decisions",
    MemoryType.PROJECT: "Projects",
}


@dataclass(frozen=True)
class SyncReport:
    exported: int = 0
    imported: int = 0
    unchanged: int = 0
    conflicts: int = 0
    skipped: int = 0


class ObsidianAdapter:
    """Maps Redstone memories to a safe, inspectable Obsidian vault."""

    def __init__(
        self, vault_path: Path | str, store: MemoryStore, privacy: PrivacyPolicy | None = None
    ) -> None:
        self.vault = Path(vault_path).expanduser().resolve()
        self.store = store
        self.privacy = privacy or PrivacyPolicy()

    @property
    def _sync_path(self) -> Path:
        return self.vault / ".redstone" / "sync.json"

    def initialize_vault(self) -> list[Path]:
        """Create required directories without overwriting existing files."""
        paths = [
            self.vault / "Memories" / name
            for name in (
                "Semantic",
                "Episodic",
                "Procedural",
                "Preferences",
                "Decisions",
                "Projects",
                "Other",
            )
        ] + [
            self.vault / name
            for name in ("Projects", "Entities", "Conflicts", "Archive", ".redstone")
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
        config = self.vault / ".redstone" / "config.json"
        if not config.exists():
            config.write_text(json.dumps({"format": 1}, indent=2) + "\n", encoding="utf-8")
        return paths

    def _sync_state(self) -> dict[str, dict[str, str]]:
        try:
            data = json.loads(self._sync_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_sync_state(self, state: dict[str, dict[str, str]]) -> None:
        self._sync_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._sync_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self._sync_path)

    def _memory_path(self, memory: Memory) -> Path:
        folder = _TYPE_DIRECTORIES.get(memory.type, "Other")
        return self.vault / "Memories" / folder / safe_filename(memory)

    def _write(self, memory: Memory, state: dict[str, dict[str, str]]) -> Path:
        previous = state.get(memory.id, {})
        path = self.vault / previous["path"] if "path" in previous else self._memory_path(memory)
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = memory_to_markdown(memory)
        existing = read_markdown(path)
        if existing != rendered:
            temporary = path.with_suffix(".tmp")
            temporary.write_text(rendered, encoding="utf-8")
            temporary.replace(path)
        state[memory.id] = {
            "path": path.relative_to(self.vault).as_posix(),
            "memory_hash": memory_hash(memory),
            "file_hash": normalized_hash(rendered),
        }
        return path

    def write_memory(self, memory: Memory) -> Path:
        self.initialize_vault()
        state = self._sync_state()
        path = self._write(memory, state)
        self._save_sync_state(state)
        return path

    def read_memory(self, path: Path | str) -> Memory | None:
        return markdown_to_memory(read_markdown(Path(path)) or "")

    def update_memory(self, memory: Memory) -> Path:
        return self.write_memory(memory)

    def archive_memory(self, memory: Memory) -> Path | None:
        state = self._sync_state()
        entry = state.get(memory.id)
        if entry is None:
            return None
        source = self.vault / entry["path"]
        destination = self.vault / "Archive" / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.exists() and source != destination:
            source.replace(destination)
        entry["path"] = destination.relative_to(self.vault).as_posix()
        self._save_sync_state(state)
        return destination

    def delete_memory(self, memory: Memory) -> Path | None:
        """Phase 2 deletion is archival, never permanent removal."""
        return self.archive_memory(memory)

    def export_memory(self, memory: Memory) -> Path:
        return self.write_memory(memory)

    def export(
        self,
        *,
        project: str | None = None,
        memory_type: MemoryType | None = None,
        memory_id: str | None = None,
    ) -> SyncReport:
        self.initialize_vault()
        state = self._sync_state()
        memories = self.store.list(project=project)
        if memory_type:
            memories = [memory for memory in memories if memory.type == memory_type]
        if memory_id:
            memories = [memory for memory in memories if memory.id == memory_id]
        for memory in memories:
            self._write(memory, state)
        self._save_sync_state(state)
        return SyncReport(exported=len(memories))

    def _import_memory(self, incoming: Memory, existing: Memory | None) -> bool:
        self.privacy.ensure_storable(incoming.content)
        version = max(incoming.version, (existing.version + 1) if existing else 1)
        updated = incoming.model_copy(update={"version": version, "updated_at": utc_now()})
        self.store.save(updated)
        return existing is None or memory_hash(existing) != memory_hash(updated)

    def import_vault(self, path: Path | str | None = None) -> SyncReport:
        root = Path(path).expanduser().resolve() if path else self.vault
        imported = skipped = 0
        for markdown in root.rglob("*.md"):
            text = read_markdown(markdown)
            memory = markdown_to_memory(text or "")
            if memory is None:
                skipped += 1
                continue
            try:
                if self._import_memory(memory, self.store.get(memory.id)):
                    imported += 1
            except ValueError:
                skipped += 1
        return SyncReport(imported=imported, skipped=skipped)

    def _conflict(self, memory: Memory, text: str) -> None:
        path = self.vault / "Conflicts" / f"{memory.id}-conflict.md"
        payload = (
            f"# Redstone Obsidian Conflict: {memory.id}\n\n"
            "Action required: choose a version manually. Neither version was overwritten.\n\n"
            "## Redstone Version\n\n```markdown\n"
            f"{memory_to_markdown(memory)}```\n\n## Obsidian Version\n\n```markdown\n{text}```\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    def sync(self) -> SyncReport:
        self.initialize_vault()
        state = self._sync_state()
        report = SyncReport()
        for memory_id, entry in list(state.items()):
            memory = self.store.get(memory_id)
            path = self.vault / entry["path"]
            text = read_markdown(path)
            if memory is None or text is None:
                report = SyncReport(**{**asdict(report), "skipped": report.skipped + 1})
                continue
            memory_changed = memory_hash(memory) != entry["memory_hash"]
            file_changed = normalized_hash(text) != entry["file_hash"]
            if not memory_changed and not file_changed:
                report = SyncReport(**{**asdict(report), "unchanged": report.unchanged + 1})
            elif memory_changed and not file_changed:
                self._write(memory, state)
                report = SyncReport(**{**asdict(report), "exported": report.exported + 1})
            elif file_changed and not memory_changed:
                incoming = markdown_to_memory(text)
                if incoming is None:
                    report = SyncReport(**{**asdict(report), "skipped": report.skipped + 1})
                    continue
                try:
                    self._import_memory(incoming, memory)
                    updated = self.store.get(memory_id)
                    if updated:
                        self._write(updated, state)
                    report = SyncReport(**{**asdict(report), "imported": report.imported + 1})
                except ValueError:
                    report = SyncReport(**{**asdict(report), "skipped": report.skipped + 1})
            else:
                self._conflict(memory, text)
                report = SyncReport(**{**asdict(report), "conflicts": report.conflicts + 1})
        self._save_sync_state(state)
        return report

    def status(self) -> dict[str, int | str]:
        state = self._sync_state()
        conflicts = (
            len(list((self.vault / "Conflicts").glob("*-conflict.md")))
            if self.vault.exists()
            else 0
        )
        return {
            "vault": str(self.vault),
            "memories": len(state),
            "synced": len(state),
            "conflicts": conflicts,
        }
