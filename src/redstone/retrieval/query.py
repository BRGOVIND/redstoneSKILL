"""Deterministic query intent detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from redstone.retrieval.search import _terms


class QueryIntent(StrEnum):
    CURRENT = "current_state"
    HISTORICAL = "historical_state"
    TIMELINE = "timeline"
    PROVENANCE = "provenance"
    CONTRADICTION = "contradiction"
    GENERAL = "general"
    COMPARISON = "comparison"
    MULTI_MEMORY = "multi_memory"
    DECISION = "decision"
    PREFERENCE = "preference"
    PROJECT = "project"
    RELATED = "related"


class InformationRequirement(StrEnum):
    FACT = "fact"
    CURRENT = "current_state"
    HISTORICAL = "historical_state"
    TIMELINE = "timeline"
    DECISION = "decision"
    PREFERENCE = "preference"
    REASON = "reason"
    PROJECT = "project"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    PROVENANCE = "provenance"
    CONTRADICTION = "contradiction"


@dataclass(frozen=True)
class QueryAnalysis:
    """Deterministic information needs for coverage-aware retrieval."""

    intent: QueryIntent
    requirements: tuple[InformationRequirement, ...]
    multi_memory: bool
    minimum_memories: int = 1


def parse_intent(query: str) -> QueryIntent:
    """Classify temporal/provenance wording without an LLM."""
    lowered = query.casefold()
    if any(
        term in lowered
        for term in (
            "originally",
            "original ",
            "previously",
            "former",
            "used to",
            "at first",
            "what was",
            "active in",
        )
    ):
        return QueryIntent.HISTORICAL
    if any(
        term in lowered
        for term in ("when did", "timeline", "what changed", "change its", "history", "over time")
    ):
        return QueryIntent.TIMELINE
    if any(
        term in lowered for term in (" now", "current", "currently", "this week", "latest", "today")
    ):
        return QueryIntent.CURRENT
    if any(term in lowered for term in ("which conversation", "source", "provenance", "supports")):
        return QueryIntent.PROVENANCE
    return QueryIntent.GENERAL


def analyze_query(query: str) -> QueryAnalysis:
    """Represent query needs without an LLM planner."""
    lowered = query.casefold()
    requirements: list[InformationRequirement] = []
    has_current = any(
        term in lowered for term in (" now", "current", "currently", "latest", "today", "this week")
    )
    has_history = any(
        term in lowered
        for term in ("before", "original", "previous", "former", "used to", "at first")
    )
    if has_current:
        requirements.append(InformationRequirement.CURRENT)
    if has_history:
        requirements.append(InformationRequirement.HISTORICAL)
    has_timeline = any(
        term in lowered for term in ("when did", "timeline", "what changed", "history", "over time")
    )
    if has_timeline:
        requirements.append(InformationRequirement.TIMELINE)
        requirements.extend((InformationRequirement.CURRENT, InformationRequirement.HISTORICAL))
    if any(term in lowered for term in ("decision", "decide", "chose", "selected")):
        requirements.append(InformationRequirement.DECISION)
    if any(term in lowered for term in ("prefer", "preference", "favorite")):
        requirements.append(InformationRequirement.PREFERENCE)
    if any(
        term in lowered for term in (" why", "reason", "constraint", "caused", "because", "due to")
    ):
        requirements.append(InformationRequirement.REASON)
    if "project" in lowered:
        requirements.append(InformationRequirement.PROJECT)
    if any(term in lowered for term in (" who", "owner", "person", "entity")):
        requirements.append(InformationRequirement.ENTITY)
    if any(term in lowered for term in ("related", "relationship", "depends", "approved")):
        requirements.append(InformationRequirement.RELATIONSHIP)
    if any(term in lowered for term in ("source", "provenance", "which conversation", "supports")):
        requirements.append(InformationRequirement.PROVENANCE)
    if any(term in lowered for term in ("conflict", "contradict", "inconsistent")):
        requirements.append(InformationRequirement.CONTRADICTION)
    if not requirements:
        requirements.append(InformationRequirement.FACT)
    requirements = list(dict.fromkeys(requirements))
    comparison = has_current and has_history
    multi = (
        comparison
        or has_timeline
        or any(term in lowered for term in (" and ", " both ", "compare", "conflict", "versus"))
    )
    if comparison:
        intent = QueryIntent.COMPARISON
    elif multi:
        intent = QueryIntent.MULTI_MEMORY
    elif InformationRequirement.DECISION in requirements:
        intent = QueryIntent.DECISION
    elif InformationRequirement.PREFERENCE in requirements:
        intent = QueryIntent.PREFERENCE
    elif InformationRequirement.PROJECT in requirements:
        intent = QueryIntent.PROJECT
    elif InformationRequirement.RELATIONSHIP in requirements:
        intent = QueryIntent.RELATED
    else:
        intent = parse_intent(query)
    minimum_memories = 3 if "over time" in lowered else 2 if multi else 1
    return QueryAnalysis(intent, tuple(requirements), multi, minimum_memories)


def query_terms(query: str) -> set[str]:
    """Expand small evidence-backed domain synonyms for lexical retrieval."""
    terms = _terms(query)
    aliases = {
        "storage": {"database"},
        "engine": {"database"},
        "persistence": {"database"},
        "technology": {"database"},
        "begin": {"originally"},
        "ui": {"dashboard", "framework"},
        "stack": {"framework"},
        "powers": {"uses"},
        "approved": {"approval", "owner"},
    }
    for term in tuple(terms):
        terms.update(aliases.get(term, ()))
    return terms
