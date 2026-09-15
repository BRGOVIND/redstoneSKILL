"""Stable Markdown serialization for Obsidian-compatible memory documents."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from redstone.core.memory import Memory, MemoryStatus, MemoryType

_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_FILE_SIZE = 1_000_000


def normalized_hash(text: str) -> str:
    """Hash content after line-ending and trailing-whitespace normalization."""
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def memory_hash(memory: Memory) -> str:
    """Hash memory state relevant to human synchronization."""
    payload = memory.model_dump(mode="json", exclude={"access_count", "last_accessed_at"})
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def safe_filename(memory: Memory, *, max_length: int = 120) -> str:
    """Return deterministic, traversal-safe Markdown filename."""
    stem = _INVALID_FILENAME.sub("-", memory.summary.lower())
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-.") or "memory"
    prefix = f"{memory.id}-"
    stem = stem[: max(1, max_length - len(prefix) - 3)].strip("-") or "memory"
    return f"{prefix}{stem}.md"


def memory_to_markdown(memory: Memory) -> str:
    """Serialize memory as readable, deterministic Obsidian Markdown."""
    fields: dict[str, Any] = {
        "redstone_id": memory.id,
        "redstone_version": memory.version,
        "type": memory.type.value,
        "project": memory.project,
        "summary": memory.summary,
        "confidence": memory.confidence,
        "importance": memory.importance,
        "status": memory.status.value,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "observed_at": memory.observed_at.isoformat(),
        "valid_from": memory.valid_from.isoformat() if memory.valid_from else None,
        "valid_until": memory.valid_until.isoformat() if memory.valid_until else None,
        "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
        "source": memory.source,
        "tags": memory.tags,
        "entities": memory.entities,
        "related_memories": memory.related_memories,
        "relationships": memory.relationships,
        "supersedes": memory.supersedes,
        "superseded_by": memory.superseded_by,
        "derived_from": memory.derived_from,
    }
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()
    )
    tags = " ".join(f"#{tag.replace(' ', '-')}" for tag in memory.tags) or "None"
    related = "\n".join(f"- [[{item}]]" for item in memory.related_memories) or "- None"
    return (
        f"---\n{frontmatter}\n---\n\n# {memory.summary}\n\n"
        "<!-- redstone:content:start -->\n"
        f"{memory.content}\n"
        "<!-- redstone:content:end -->\n\n"
        f"## Tags\n\n{tags}\n\n## Related Memories\n\n{related}\n\n"
        f"## Provenance\n\nSource: {memory.source}\n"
    )


def _parse_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value.strip().strip('"')


def markdown_to_memory(text: str) -> Memory | None:
    """Parse only Redstone documents; ordinary Markdown returns ``None``."""
    if len(text.encode("utf-8")) > _MAX_FILE_SIZE or not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    data: dict[str, Any] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            return None
        data[key.strip()] = _parse_value(value.strip())
    if not isinstance(data.get("redstone_id"), str):
        return None
    start_marker = "<!-- redstone:content:start -->\n"
    end_marker = "\n<!-- redstone:content:end -->"
    start = text.find(start_marker, end + 5)
    finish = text.find(end_marker, start + len(start_marker))
    if start < 0 or finish < 0:
        return None
    content = text[start + len(start_marker) : finish]
    try:
        return Memory(
            id=data["redstone_id"],
            version=int(data.get("redstone_version", 1)),
            type=MemoryType(data.get("type", "semantic")),
            content=content,
            summary=str(data.get("summary") or content[:240]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            observed_at=data["observed_at"],
            valid_from=data.get("valid_from"),
            valid_until=data.get("valid_until"),
            confidence=float(data.get("confidence", 0.8)),
            importance=float(data.get("importance", 0.5)),
            status=MemoryStatus(data.get("status", "active")),
            source=str(data.get("source", "obsidian")),
            project=data.get("project"),
            tags=list(data.get("tags", [])),
            entities=list(data.get("entities", [])),
            related_memories=list(data.get("related_memories", [])),
            relationships=dict(data.get("relationships", {})),
            supersedes=data.get("supersedes"),
            superseded_by=data.get("superseded_by"),
            expires_at=data.get("expires_at"),
            derived_from=list(data.get("derived_from", [])),
        )
    except (KeyError, TypeError, ValueError):
        return None


def read_markdown(path: Path) -> str | None:
    """Read a bounded UTF-8 Markdown file without trusting its contents."""
    try:
        if not path.is_file() or path.stat().st_size > _MAX_FILE_SIZE:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
