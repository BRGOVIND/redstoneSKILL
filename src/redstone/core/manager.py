"""Memory lifecycle service."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from redstone.core.formation import MemoryCandidate, reject_reason
from redstone.core.memory import Memory, MemoryType, utc_now
from redstone.privacy.policy import PrivacyPolicy
from redstone.reasoning.temporal import TemporalComposition, compose_temporal
from redstone.retrieval.context import build_adaptive_context
from redstone.retrieval.ranking import hybrid_search
from redstone.retrieval.search import SearchResult
from redstone.retrieval.selector import AdaptiveSelection, adaptive_retrieve
from redstone.storage.base import MemoryStore


class MemoryManager:
    """Coordinates validation, privacy, persistence, and deterministic retrieval."""

    def __init__(self, store: MemoryStore, privacy: PrivacyPolicy | None = None) -> None:
        self.store = store
        self.privacy = privacy or PrivacyPolicy()

    @staticmethod
    def _id(content: str, memory_type: MemoryType, project: str | None) -> str:
        normalized = re.sub(r"\s+", " ", content.strip().lower())
        payload = f"{memory_type.value}\0{project or ''}\0{normalized}".encode()
        return f"mem_{hashlib.sha256(payload).hexdigest()[:20]}"

    def remember(
        self,
        content: str,
        memory_type: MemoryType | str = MemoryType.SEMANTIC,
        *,
        source: str = "manual",
        project: str | None = None,
        summary: str | None = None,
        tags: list[str] | None = None,
        entities: list[str] | None = None,
        confidence: float = 0.8,
        importance: float = 0.5,
        observed_at: datetime | None = None,
    ) -> tuple[Memory, bool]:
        """Persist a memory; returns ``(memory, created)`` for duplicate-safe callers."""
        self.privacy.ensure_storable(content)
        typed = MemoryType(memory_type)
        memory_id = self._id(content, typed, project)
        existing = self.store.get(memory_id)
        if existing:
            return existing, False
        now = utc_now()
        memory = Memory(
            id=memory_id,
            type=typed,
            content=content,
            summary=summary or content[:240],
            source=source,
            project=project,
            tags=tags or [],
            entities=entities or [],
            confidence=confidence,
            importance=importance,
            created_at=now,
            updated_at=now,
            observed_at=observed_at or now,
        )
        self.store.save(memory)
        return memory, True

    def remember_candidate(
        self, candidate: MemoryCandidate
    ) -> tuple[Memory | None, bool, str | None]:
        """Apply formation and privacy policy before deterministic persistence."""
        reason = reject_reason(candidate)
        if reason:
            return None, False, reason
        try:
            memory, created = self.remember(
                candidate.content,
                candidate.memory_type,
                source=candidate.source,
                project=candidate.project,
                importance=candidate.importance,
            )
        except ValueError:
            return None, False, "privacy_rejection"
        return memory, created, None if created else "exact_duplicate"

    def search(
        self, query: str, *, project: str | None = None, limit: int = 10
    ) -> list[SearchResult]:
        memories = self.store.list(project=project)
        results = hybrid_search(query, memories, project=project, limit=limit)
        if not results or len(results) >= limit:
            return results
        by_id = {memory.id: memory for memory in memories}
        expanded = list(results)
        seen = {result.memory.id for result in results}
        for result in results:
            links = set(result.memory.related_memories + result.memory.derived_from)
            links.update(item for values in result.memory.relationships.values() for item in values)
            links.update(
                item for item in (result.memory.supersedes, result.memory.superseded_by) if item
            )
            for linked_id in sorted(links):
                if linked_id in by_id and linked_id not in seen and len(expanded) < limit:
                    expanded.append(
                        SearchResult(
                            by_id[linked_id],
                            round(result.score * 0.8, 6),
                            f"related to {result.memory.id}",
                        )
                    )
                    seen.add(linked_id)
        return expanded

    def recall(
        self,
        query: str,
        *,
        project: str | None = None,
        limit: int = 5,
        max_tokens: int = 500,
    ) -> str:
        selection = self.retrieve_adaptive(
            query, project=project, max_memories=limit, max_tokens=max_tokens
        )
        if not selection.results:
            return "REDSTONE MEMORY DATA\nNo matching memories found."
        for result in selection.results:
            self.store.touch(result.memory.id)
        return build_adaptive_context(selection, project=project, max_tokens=max_tokens)

    def retrieve_adaptive(
        self,
        query: str,
        *,
        project: str | None = None,
        max_memories: int = 5,
        max_tokens: int = 500,
        relationship_depth: int = 1,
    ) -> AdaptiveSelection:
        """Retrieve minimum complementary evidence satisfying query requirements."""
        return adaptive_retrieve(
            query,
            self.store.list(project=project),
            project=project,
            max_memories=max_memories,
            max_tokens=max_tokens,
            relationship_depth=relationship_depth,
        )

    def compose_temporal(
        self, query: str, *, project: str | None = None, max_memories: int = 10
    ) -> TemporalComposition:
        """Retrieve then expand linked evidence into deterministic temporal state."""
        memories = self.store.list(project=project)
        selection = self.retrieve_adaptive(
            query,
            project=project,
            max_memories=max_memories,
            max_tokens=1_000,
            relationship_depth=1,
        )
        selected = {result.memory.id: result.memory for result in selection.results}
        by_id = {memory.id: memory for memory in memories}
        lowered_query = query.casefold()
        for memory in memories:
            scoped_entities = [entity for entity in memory.entities if entity != memory.project]
            if scoped_entities and any(
                entity.casefold() in lowered_query for entity in scoped_entities
            ):
                selected[memory.id] = memory
        frontier = list(selected.values())
        while frontier:
            memory = frontier.pop()
            for linked_id in (memory.supersedes, memory.superseded_by):
                if linked_id and linked_id in by_id and linked_id not in selected:
                    selected[linked_id] = by_id[linked_id]
                    frontier.append(by_id[linked_id])
        return compose_temporal(list(selected.values()), query)

    def archive(self, memory_id: str) -> Memory:
        """Archive a memory while retaining history and provenance."""
        return self.store.archive(memory_id)

    def update(self, memory_id: str, content: str, *, summary: str | None = None) -> Memory:
        """Version a content update; preserves ID and all historical metadata."""
        self.privacy.ensure_storable(content)
        memory = self.store.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        updated = memory.model_copy(
            update={
                "content": content,
                "summary": summary or content[:240],
                "version": memory.version + 1,
                "updated_at": utc_now(),
            }
        )
        self.store.save(updated)
        return updated

    def supersede(self, older_id: str, newer_id: str) -> None:
        """Link historical truth without deleting old memory."""
        older, newer = self.store.get(older_id), self.store.get(newer_id)
        if older is None or newer is None:
            raise KeyError(older_id if older is None else newer_id)
        self.store.save(
            older.model_copy(update={"superseded_by": newer.id, "updated_at": utc_now()})
        )
        self.store.save(newer.model_copy(update={"supersedes": older.id, "updated_at": utc_now()}))

    def timeline(self, project: str) -> list[Memory]:
        return sorted(
            self.store.list(project=project, include_archived=True),
            key=lambda memory: (memory.observed_at, memory.id),
        )

    def related(self, memory_id: str) -> list[Memory]:
        memory = self.store.get(memory_id)
        if memory is None:
            raise KeyError(memory_id)
        ids = set(memory.related_memories + memory.derived_from)
        ids.update(item for values in memory.relationships.values() for item in values)
        ids.update(item for item in (memory.supersedes, memory.superseded_by) if item)
        related = [item for item in self.store.list(include_archived=True) if item.id in ids]
        if not related and memory.project:
            related = [
                item for item in self.store.list(project=memory.project) if item.id != memory.id
            ][:5]
        return sorted(related, key=lambda item: item.id)

    def link(self, memory_id: str, related_id: str, relationship: str = "related_to") -> None:
        """Create lightweight typed relation without graph database dependency."""
        if relationship not in {"related_to", "part_of", "supersedes", "derived_from"}:
            raise ValueError("unsupported relationship")
        memory, related = self.store.get(memory_id), self.store.get(related_id)
        if memory is None or related is None:
            raise KeyError(memory_id if memory is None else related_id)
        relations = {key: list(value) for key, value in memory.relationships.items()}
        relations[relationship] = sorted(set(relations.get(relationship, []) + [related_id]))
        self.store.save(
            memory.model_copy(update={"relationships": relations, "updated_at": utc_now()})
        )

    def conflicts(self) -> list[tuple[Memory, Memory]]:
        """Report explicit competing memories sharing type and project."""
        memories = self.store.list(include_archived=True)
        return [
            (left, right)
            for index, left in enumerate(memories)
            for right in memories[index + 1 :]
            if left.type == right.type
            and left.project == right.project
            and left.content != right.content
            and not (left.superseded_by == right.id or right.superseded_by == left.id)
        ]

    def stats(self) -> dict[str, int]:
        memories = self.store.list(include_archived=True)
        return {
            "total": len(memories),
            "active": sum(m.status.value == "active" for m in memories),
            "archived": sum(m.status.value == "archived" for m in memories),
        }
