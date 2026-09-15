"""Deterministic hybrid ranking without embedding dependencies."""

from __future__ import annotations

import math
from dataclasses import dataclass

from redstone.core.memory import Memory, utc_now
from redstone.retrieval.query import QueryIntent, parse_intent, query_terms
from redstone.retrieval.search import SearchResult, _terms

_TIME_TERMS = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}


@dataclass(frozen=True)
class RankingWeights:
    keyword: float = 0.45
    recency: float = 0.15
    importance: float = 0.20
    confidence: float = 0.10
    project: float = 0.10
    decay_days: float = 180.0


def hybrid_search(
    query: str,
    memories: list[Memory],
    *,
    project: str | None = None,
    limit: int = 10,
    weights: RankingWeights | None = None,
    intent: QueryIntent | None = None,
) -> list[SearchResult]:
    """Rank lexical matches with explicit recency, metadata, and project signals."""
    weights = weights or RankingWeights()
    terms = query_terms(query)
    lowered_query = query.casefold()
    now = utc_now()
    intent = intent or parse_intent(query)
    results: list[SearchResult] = []
    for memory in memories:
        if intent == QueryIntent.CURRENT and memory.superseded_by:
            continue
        if intent == QueryIntent.HISTORICAL and not memory.superseded_by:
            continue
        body = _terms(f"{memory.content} {memory.summary} {' '.join(memory.tags)}")
        overlap = terms & body
        if not overlap:
            continue
        keyword = len(overlap) / len(terms | body)
        age_days = max(0.0, (now - memory.observed_at).total_seconds() / 86400)
        recency = math.exp(-age_days / weights.decay_days)
        project_match = 1.0 if project and memory.project == project else 0.0
        specific_entities = [
            entity
            for entity in memory.entities
            if entity != memory.project and len(_terms(entity)) > 1
        ]
        entity_match = any(entity.casefold() in lowered_query for entity in specific_entities)
        entity_conflict = bool(specific_entities) and not entity_match
        date_match = bool((terms & _TIME_TERMS) & body)
        temporal_match = 0.0
        if (
            intent == QueryIntent.CURRENT
            and not memory.superseded_by
            or intent == QueryIntent.HISTORICAL
            and memory.superseded_by
        ):
            temporal_match = 0.10
        elif intent == QueryIntent.PROVENANCE and memory.source:
            temporal_match = 0.05
        score = (
            weights.keyword * keyword
            + weights.recency * recency
            + weights.importance * memory.importance
            + weights.confidence * memory.confidence
            + weights.project * project_match
            + temporal_match
            + (0.15 if entity_match else -0.20 if entity_conflict else 0.0)
            + (0.15 if date_match else 0.0)
        )
        signals = ["keyword match=" + ",".join(sorted(overlap))]
        if project_match:
            signals.append("project")
        if temporal_match:
            signals.append(f"intent={intent.value}")
        if entity_match:
            signals.append("entity")
        elif entity_conflict:
            signals.append("entity conflict")
        if date_match:
            signals.append("date")
        signals.append(f"recency={recency:.2f}")
        results.append(SearchResult(memory, round(score, 6), "; ".join(signals)))
    return sorted(results, key=lambda item: (-item.score, item.memory.id))[:limit]
