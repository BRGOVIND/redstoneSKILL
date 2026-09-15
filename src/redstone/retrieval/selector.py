"""Coverage-aware complementary memory selection."""

from __future__ import annotations

from dataclasses import dataclass

from redstone.core.memory import Memory, MemoryType
from redstone.retrieval.query import (
    InformationRequirement,
    QueryAnalysis,
    QueryIntent,
    analyze_query,
)
from redstone.retrieval.ranking import hybrid_search
from redstone.retrieval.search import SearchResult, _terms


@dataclass(frozen=True)
class AdaptiveSelection:
    analysis: QueryAnalysis
    results: tuple[SearchResult, ...]
    covered: frozenset[InformationRequirement]
    context_tokens: int
    redundancy_rate: float

    @property
    def coverage(self) -> float:
        required = set(self.analysis.requirements)
        return len(required & self.covered) / len(required) if required else 1.0


def _token_count(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _memory_requirements(memory: Memory) -> set[InformationRequirement]:
    covered = {InformationRequirement.FACT, InformationRequirement.PROVENANCE}
    if memory.superseded_by:
        covered.add(InformationRequirement.HISTORICAL)
    elif memory.supersedes or any(
        term in memory.content.casefold()
        for term in (" now ", "currently", "current ", "latest", "this week")
    ):
        covered.add(InformationRequirement.CURRENT)
    if memory.type == MemoryType.DECISION:
        covered.add(InformationRequirement.DECISION)
    if memory.type == MemoryType.PREFERENCE:
        covered.add(InformationRequirement.PREFERENCE)
    if memory.project:
        covered.add(InformationRequirement.PROJECT)
    if any(entity != memory.project for entity in memory.entities):
        covered.add(InformationRequirement.ENTITY)
    if memory.related_memories or memory.relationships or memory.supersedes or memory.superseded_by:
        covered.add(InformationRequirement.RELATIONSHIP)
    lowered = memory.content.casefold()
    if memory.type == MemoryType.CONSTRAINT or any(
        term in lowered for term in ("because", "due to", "constraint", "reason")
    ):
        covered.add(InformationRequirement.REASON)
    if memory.supersedes or memory.superseded_by:
        covered.add(InformationRequirement.TIMELINE)
    if any(term in lowered for term in ("conflict", "contradict", "stale", "unverified", "claim")):
        covered.add(InformationRequirement.CONTRADICTION)
    return covered


def _similarity(left: Memory, right: Memory) -> float:
    left_terms, right_terms = _terms(left.content), _terms(right.content)
    return (
        len(left_terms & right_terms) / len(left_terms | right_terms)
        if left_terms | right_terms
        else 1.0
    )


def adaptive_retrieve(
    query: str,
    memories: list[Memory],
    *,
    project: str | None = None,
    max_memories: int = 5,
    max_tokens: int = 500,
    relationship_depth: int = 1,
    candidate_results: list[SearchResult] | None = None,
    lexical_candidates: bool = True,
) -> AdaptiveSelection:
    """Select minimum complementary evidence covering deterministic query needs."""
    analysis = analyze_query(query)
    intents = [
        parse
        for parse in (QueryIntent.CURRENT, QueryIntent.HISTORICAL)
        if (
            parse == QueryIntent.CURRENT and InformationRequirement.CURRENT in analysis.requirements
        )
        or (
            parse == QueryIntent.HISTORICAL
            and InformationRequirement.HISTORICAL in analysis.requirements
        )
    ]
    if not intents:
        intents = [
            QueryIntent.TIMELINE
            if InformationRequirement.TIMELINE in analysis.requirements
            else parse_intent_fallback(analysis)
        ]
    candidates: dict[str, SearchResult] = {}
    for intent in intents:
        sources = []
        if lexical_candidates:
            sources.extend(
                hybrid_search(
                    query, memories, project=project, limit=max(20, max_memories * 4), intent=intent
                )
            )
        if candidate_results:
            sources.extend(candidate_results)
        for result in sources:
            if intent == QueryIntent.CURRENT and result.memory.superseded_by:
                continue
            if intent == QueryIntent.HISTORICAL and not result.memory.superseded_by:
                continue
            is_conflict_evidence = (
                InformationRequirement.CONTRADICTION in analysis.requirements
                and InformationRequirement.CONTRADICTION in _memory_requirements(result.memory)
            )
            if (
                InformationRequirement.TIMELINE in analysis.requirements
                and not is_conflict_evidence
            ):
                if intent == QueryIntent.CURRENT and not result.memory.supersedes:
                    continue
                if intent == QueryIntent.HISTORICAL and not result.memory.superseded_by:
                    continue
            previous = candidates.get(result.memory.id)
            if previous is None or result.score > previous.score:
                candidates[result.memory.id] = result
    by_id = {memory.id: memory for memory in memories}
    frontier = list(candidates.values())
    for _ in range(max(0, relationship_depth)):
        additions: list[SearchResult] = []
        for result in frontier:
            memory = result.memory
            links = set(memory.related_memories + memory.derived_from)
            links.update(item for values in memory.relationships.values() for item in values)
            links.update(item for item in (memory.supersedes, memory.superseded_by) if item)
            for linked_id in sorted(links):
                if linked_id in by_id:
                    linked = SearchResult(
                        by_id[linked_id], round(result.score * 0.85, 6), f"related to {memory.id}"
                    )
                    previous = candidates.get(linked_id)
                    if previous is None or linked.score > previous.score:
                        candidates[linked_id] = linked
                        additions.append(linked)
        frontier = additions
    required = set(analysis.requirements)
    selected: list[SearchResult] = []
    covered: set[InformationRequirement] = set()
    used_tokens = 0
    redundant_rejections = 0
    minimum = 1
    if analysis.multi_memory:
        minimum = (
            3 if {InformationRequirement.REASON, InformationRequirement.ENTITY} <= required else 2
        )
    minimum = max(minimum, analysis.minimum_memories)
    minimum = min(minimum, max_memories)
    if InformationRequirement.TIMELINE in required:
        minimum = min(max_memories, len(candidates))
    while (
        candidates
        and len(selected) < max_memories
        and (not required <= covered or len(selected) < minimum)
    ):
        best: SearchResult | None = None
        best_value = -1.0
        for candidate in candidates.values():
            evidence = _memory_requirements(candidate.memory)
            new_coverage = len((evidence & required) - covered)
            redundancy = max(
                (_similarity(candidate.memory, item.memory) for item in selected), default=0.0
            )
            same_fact_composition = InformationRequirement.CONTRADICTION in required
            redundancy_weight = 0.05 if new_coverage or same_fact_composition else 0.35
            value = candidate.score + 0.45 * new_coverage - redundancy_weight * redundancy
            if value > best_value or (
                value == best_value and best and candidate.memory.id < best.memory.id
            ):
                best, best_value = candidate, value
        if best is None:
            break
        candidates.pop(best.memory.id)
        size = _token_count(best.memory.content)
        evidence = _memory_requirements(best.memory)
        redundancy = max((_similarity(best.memory, item.memory) for item in selected), default=0.0)
        if redundancy >= 0.8 and not ((evidence & required) - covered):
            redundant_rejections += 1
            continue
        if used_tokens + size > max_tokens:
            continue
        selected.append(best)
        covered.update(evidence)
        if InformationRequirement.CONTRADICTION in required and len(selected) >= 2:
            covered.add(InformationRequirement.CONTRADICTION)
        used_tokens += size
    pairs = len(selected) * (len(selected) - 1) // 2
    redundant_pairs = sum(
        _similarity(left.memory, right.memory) >= 0.8
        for index, left in enumerate(selected)
        for right in selected[index + 1 :]
    )
    rate = redundant_pairs / pairs if pairs else 0.0
    return AdaptiveSelection(analysis, tuple(selected), frozenset(covered), used_tokens, rate)


def parse_intent_fallback(analysis: QueryAnalysis) -> QueryIntent:
    if InformationRequirement.PROVENANCE in analysis.requirements:
        return QueryIntent.PROVENANCE
    return QueryIntent.GENERAL
