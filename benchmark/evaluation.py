"""Fair deterministic RMB evaluation and failure analysis."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.retrieval.search import _terms
from redstone.storage.sqlite import SQLiteMemoryStore

from .dataset import Dataset, Question

FAILURE_CATEGORIES = (
    "insufficient_coverage",
    "wrong_memory_combination",
    "temporal_composition",
    "redundant_selection",
    "missing_relationship",
    "context_composition",
)


def token_count(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def ingest(dataset: Dataset, root: Path) -> tuple[MemoryManager, dict[str, str]]:
    manager = MemoryManager(SQLiteMemoryStore(root / "index.db"))
    source_to_memory: dict[str, str] = {}
    for conversation in dataset.conversations:
        memory_type = MemoryType(conversation.kind) if conversation.kind in {item.value for item in MemoryType} else MemoryType.EPISODIC
        memory, _ = manager.remember(conversation.content, memory_type, source=conversation.id, project=conversation.project, entities=list(conversation.entities), observed_at=conversation.observed_at, importance=0.9 if conversation.kind != "noise" else 0.1)
        source_to_memory[conversation.id] = memory.id
        if conversation.supersedes_source:
            manager.supersede(source_to_memory[conversation.supersedes_source], memory.id)
    for conversation in dataset.conversations:
        for related_source in conversation.related_sources:
            manager.link(source_to_memory[conversation.id], source_to_memory[related_source])
    return manager, source_to_memory


def _baseline_search(dataset: Dataset, question: str, budget: int, limit: int) -> tuple[list[str], int]:
    """Raw lexical retrieval: content only, no project or temporal metadata."""
    query_terms = _terms(question)
    scored: list[tuple[float, int, str, str]] = []
    for conversation in dataset.conversations:
        body_terms = _terms(conversation.content)
        overlap = query_terms & body_terms
        if overlap:
            scored.append((len(overlap) / len(query_terms | body_terms), conversation.index, conversation.id, conversation.content))
    selected: list[str] = []
    used = 0
    for _, _, source, content in sorted(scored, key=lambda item: (-item[0], -item[1], item[2]))[:limit]:
        size = token_count(content)
        if used + size > budget:
            break
        selected.append(source)
        used += size
    return selected, used


def _score(expected: set[str], retrieved: list[str]) -> tuple[float, float, float]:
    relevant = len(expected & set(retrieved))
    recall = relevant / len(expected)
    precision = relevant / len(retrieved) if retrieved else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return recall, precision, f1


def classify_failure(question: Question, retrieved: list[str], expected: set[str]) -> str:
    if not retrieved:
        return "irrelevant_retrieval"
    if question.category == "multi_hop":
        return "missing_relationship"
    if question.category in {"temporal", "supersession"} and len(expected) > 1:
        return "temporal_composition"
    if len(retrieved) < len(expected):
        return "insufficient_coverage"
    if question.category in {"current_state", "historical_state", "temporal", "supersession"}:
        return "temporal_confusion"
    if question.category == "project":
        return "project_confusion"
    if question.category == "provenance":
        return "provenance"
    if len(expected & set(retrieved)) < len(expected):
        return "wrong_memory_combination"
    return "ranking"


def evaluate(dataset: Dataset, root: Path, *, top_k: int = 5, context_budget: int = 400) -> dict[str, Any]:
    manager, source_map = ingest(dataset, root)
    rows: list[dict[str, Any]] = []
    latency = 0.0
    adaptive_latency = 0.0
    for question in dataset.questions:
        expected_sources = set(question.expected_sources)
        expected_ids = {source_map[source] for source in expected_sources}
        baseline_ids, baseline_tokens = _baseline_search(dataset, question.question, context_budget, top_k)
        start = time.perf_counter()
        results = manager.search(question.question, project=question.expected_project, limit=top_k)
        latency += time.perf_counter() - start
        retrieved_ids = [result.memory.id for result in results]
        baseline_score = _score(expected_sources, baseline_ids)
        redstone_score = _score(expected_ids, retrieved_ids)
        adaptive_start = time.perf_counter()
        adaptive = manager.retrieve_adaptive(question.question, project=question.expected_project, max_memories=5, max_tokens=context_budget)
        adaptive_latency += time.perf_counter() - adaptive_start
        adaptive_ids = [result.memory.id for result in adaptive.results]
        adaptive_score = _score(expected_ids, adaptive_ids)
        context_tokens = token_count("\n".join(result.memory.content for result in results)) if results else 0
        rows.append({**asdict(question), "expected_memory_ids": sorted(expected_ids), "retrieved_memory_ids": retrieved_ids, "retrieved_sources": [result.memory.source for result in results], "adaptive_memory_ids": adaptive_ids, "adaptive_sources": [result.memory.source for result in adaptive.results], "baseline_recall": baseline_score[0], "baseline_precision": baseline_score[1], "baseline_f1": baseline_score[2], "baseline_context_tokens": baseline_tokens, "redstone_recall": redstone_score[0], "redstone_precision": redstone_score[1], "redstone_f1": redstone_score[2], "redstone_context_tokens": context_tokens, "adaptive_recall": adaptive_score[0], "adaptive_precision": adaptive_score[1], "adaptive_f1": adaptive_score[2], "adaptive_context_tokens": adaptive.context_tokens, "adaptive_memories": len(adaptive.results), "requirement_coverage": adaptive.coverage, "redundancy_rate": adaptive.redundancy_rate, "is_multi_memory": len(expected_ids) > 1, "failure_category": None if adaptive_score[0] == 1.0 else classify_failure(question, adaptive_ids, expected_ids)})
    def average(key: str, subset: list[dict[str, Any]] | None = None) -> float:
        values = subset if subset is not None else rows
        return sum(row[key] for row in values) / len(values) if values else 0.0
    baseline_recall = average("baseline_recall")
    redstone_recall = average("redstone_recall")
    relative = None if baseline_recall == 0 else (redstone_recall - baseline_recall) / baseline_recall
    categories = {category: average("redstone_recall", [row for row in rows if row["category"] == category]) for category in sorted({row["category"] for row in rows})}
    adaptive_categories = {category: average("adaptive_recall", [row for row in rows if row["category"] == category]) for category in sorted({row["category"] for row in rows})}
    distance_groups: dict[str, list[dict[str, Any]]] = {"0-10": [], "11-25": [], "26-50": [], "51-100": [], "101+": []}
    for row in rows:
        distance = max(220 - int(source[-3:]) for source in row["expected_sources"])
        bucket = "0-10" if distance <= 10 else "11-25" if distance <= 25 else "26-50" if distance <= 50 else "51-100" if distance <= 100 else "101+"
        distance_groups[bucket].append(row)
    distance_accuracy = {bucket: average("redstone_recall", values) for bucket, values in distance_groups.items() if values}
    redstone_tokens = average("redstone_context_tokens")
    adaptive_recall = average("adaptive_recall")
    adaptive_tokens = average("adaptive_context_tokens")
    single_rows = [row for row in rows if not row["is_multi_memory"]]
    multi_rows = [row for row in rows if row["is_multi_memory"]]
    baseline_tokens = average("baseline_context_tokens")
    return {"dataset": {"conversations": len(dataset.conversations), "projects": len(dataset.projects), "entities": len(dataset.entities), "questions": len(dataset.questions), "multi_memory_questions": len(multi_rows)}, "configuration": {"top_k": top_k, "context_budget_tokens": context_budget, "seed": 8128}, "baseline": {"recall": baseline_recall, "precision": average("baseline_precision"), "f1": average("baseline_f1"), "context_tokens": baseline_tokens}, "redstone": {"recall": redstone_recall, "precision": average("redstone_precision"), "f1": average("redstone_f1"), "context_tokens": redstone_tokens, "latency_ms": latency * 1000 / len(rows), "memory_efficiency": redstone_recall / redstone_tokens if redstone_tokens else 0.0}, "adaptive": {"recall": adaptive_recall, "precision": average("adaptive_precision"), "f1": average("adaptive_f1"), "single_memory_accuracy": average("adaptive_recall", single_rows), "multi_memory_accuracy": average("adaptive_recall", multi_rows), "requirement_coverage": average("requirement_coverage"), "average_memories_selected": average("adaptive_memories"), "redundancy_rate": average("redundancy_rate"), "context_tokens": adaptive_tokens, "latency_ms": adaptive_latency * 1000 / len(rows), "memory_efficiency": adaptive_recall / adaptive_tokens if adaptive_tokens else 0.0}, "absolute_improvement": redstone_recall - baseline_recall, "relative_improvement": relative, "adaptive_absolute_improvement": adaptive_recall - redstone_recall, "adaptive_context_change": (adaptive_tokens - redstone_tokens) / redstone_tokens if redstone_tokens else 0.0, "context_reduction": (baseline_tokens - redstone_tokens) / baseline_tokens if baseline_tokens else 0.0, "category_accuracy": categories, "adaptive_category_accuracy": adaptive_categories, "distance_accuracy": distance_accuracy, "failure_categories": dict(Counter(row["failure_category"] for row in rows if row["failure_category"])), "questions": rows}
