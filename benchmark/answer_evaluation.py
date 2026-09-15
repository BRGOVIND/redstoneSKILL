"""Three-level real-world RMB evaluation: retrieval, context, and answer."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from redstone.retrieval.context import build_adaptive_context

from .answers import AnswerProvider, DeterministicAnswerProvider, normalize, score_answer
from .dataset import Conversation, Dataset
from .evaluation import _score, ingest, token_count


def _baseline_context(
    conversations: tuple[Conversation, ...],
    *,
    project: str | None,
    budget: int,
) -> tuple[str, list[str]]:
    history = [item for item in conversations if project is None or item.project == project]
    selected: list[Conversation] = []
    used = 0
    for item in reversed(history):
        line = f"[source={item.id}] {item.content}"
        size = token_count(line)
        if used + size > budget:
            break
        selected.append(item)
        used += size
    selected.reverse()
    return "\n".join(f"[source={item.id}] {item.content}" for item in selected), [item.id for item in selected]


def _context_has_ground_truth(
    context: str,
    facts: tuple[str, ...],
    sources: tuple[str, ...],
    requires_provenance: bool,
) -> bool:
    normalized = normalize(context)
    facts_present = all(normalize(fact) in normalized for fact in facts)
    source_present = not requires_provenance or any(normalize(source) in normalized for source in sources)
    return facts_present and source_present


def attribute_failure(
    retrieval_ok: bool,
    context_ok: bool,
    answer_ok: bool,
    evaluation_ok: bool = True,
) -> str | None:
    """Attribute first failed pipeline level without blaming passing levels."""
    if not evaluation_ok:
        return "evaluation_failure"
    if not retrieval_ok:
        return "retrieval_failure"
    if not context_ok:
        return "context_failure"
    if not answer_ok:
        return "answer_generation_failure"
    return None


def evaluate_answers(
    dataset: Dataset,
    root: Path,
    *,
    context_budget: int = 180,
    provider: AnswerProvider | None = None,
) -> dict[str, Any]:
    """Compare equal-budget recent history with adaptive Redstone context."""
    provider = provider or DeterministicAnswerProvider()
    manager, source_map = ingest(dataset, root)
    rows: list[dict[str, Any]] = []
    for question in dataset.questions:
        required_sources = tuple(question.expected_sources)
        expected_ids = {source_map[source] for source in required_sources}
        baseline_context, baseline_sources = _baseline_context(
            dataset.conversations,
            project=question.expected_project,
            budget=context_budget,
        )
        baseline_start = time.perf_counter()
        baseline_answer = provider.answer(question.question, baseline_context)
        baseline_latency = time.perf_counter() - baseline_start
        baseline_context_ok = _context_has_ground_truth(
            baseline_context,
            question.required_facts,
            required_sources,
            question.requires_provenance,
        )
        baseline_score = score_answer(
            baseline_answer,
            baseline_context,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            required_facts=question.required_facts,
            required_sources=required_sources,
            requires_provenance=question.requires_provenance,
        )
        baseline_retrieval = expected_ids <= {source_map[source] for source in baseline_sources}

        retrieval_start = time.perf_counter()
        selection = manager.retrieve_adaptive(
            question.question,
            project=question.expected_project,
            max_memories=5,
            max_tokens=context_budget,
            relationship_depth=1,
        )
        retrieval_latency = time.perf_counter() - retrieval_start
        retrieved_ids = [item.memory.id for item in selection.results]
        retrieved_sources = [item.memory.source for item in selection.results]
        redstone_context = build_adaptive_context(
            selection,
            project=question.expected_project,
            max_tokens=context_budget,
        )
        redstone_context_ok = _context_has_ground_truth(
            redstone_context,
            question.required_facts,
            required_sources,
            question.requires_provenance,
        )
        answer_start = time.perf_counter()
        redstone_answer = provider.answer(question.question, redstone_context)
        answer_latency = time.perf_counter() - answer_start
        redstone_score = score_answer(
            redstone_answer,
            redstone_context,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            required_facts=question.required_facts,
            required_sources=required_sources,
            requires_provenance=question.requires_provenance,
        )
        retrieval_score = _score(expected_ids, retrieved_ids)
        rows.append(
            {
                **asdict(question),
                "expected_memory_ids": sorted(expected_ids),
                "baseline_sources": baseline_sources,
                "baseline_context": baseline_context,
                "baseline_answer": baseline_answer,
                "baseline_retrieval_pass": baseline_retrieval,
                "baseline_context_pass": baseline_context_ok,
                "baseline_answer_score": asdict(baseline_score),
                "baseline_context_tokens": token_count(baseline_context),
                "baseline_latency_ms": baseline_latency * 1000,
                "baseline_failure": attribute_failure(
                    baseline_retrieval,
                    baseline_context_ok,
                    bool(baseline_score.accuracy),
                ),
                "retrieved_memory_ids": retrieved_ids,
                "retrieved_sources": retrieved_sources,
                "redstone_context": redstone_context,
                "redstone_answer": redstone_answer,
                "retrieval_recall": retrieval_score[0],
                "retrieval_precision": retrieval_score[1],
                "retrieval_f1": retrieval_score[2],
                "requirement_coverage": selection.coverage,
                "redstone_retrieval_pass": expected_ids <= set(retrieved_ids),
                "redstone_context_pass": redstone_context_ok,
                "redstone_answer_score": asdict(redstone_score),
                "redstone_context_tokens": token_count(redstone_context),
                "redstone_latency_ms": (retrieval_latency + answer_latency) * 1000,
                "redstone_failure": attribute_failure(
                    expected_ids <= set(retrieved_ids),
                    redstone_context_ok,
                    bool(redstone_score.accuracy),
                ),
            }
        )

    def average(path: tuple[str, ...], subset: list[dict[str, Any]] | None = None) -> float:
        selected = subset if subset is not None else rows
        values: list[float] = []
        for row in selected:
            value: Any = row
            for key in path:
                value = value[key]
            if value is not None:
                values.append(float(value))
        return sum(values) / len(values) if values else 0.0

    categories = sorted({row["category"] for row in rows})
    category_accuracy = {
        category: {
            "baseline": average(
                ("baseline_answer_score", "accuracy"),
                [row for row in rows if row["category"] == category],
            ),
            "redstone": average(
                ("redstone_answer_score", "accuracy"),
                [row for row in rows if row["category"] == category],
            ),
        }
        for category in categories
    }
    baseline_tokens = average(("baseline_context_tokens",))
    redstone_tokens = average(("redstone_context_tokens",))
    baseline_accuracy = average(("baseline_answer_score", "accuracy"))
    redstone_accuracy = average(("redstone_answer_score", "accuracy"))
    provenance_rows = [row for row in rows if row["requires_provenance"]]
    return {
        "dataset": {
            "projects": len(dataset.projects),
            "sessions": len(dataset.conversations),
            "questions": len(dataset.questions),
            "seed": "authored-v1",
        },
        "configuration": {
            "provider": type(provider).__name__,
            "context_budget_tokens": context_budget,
            "baseline_input": "most recent project history fitting budget",
            "redstone_input": "adaptive context from same history and budget",
        },
        "baseline": {
            "answer_accuracy": baseline_accuracy,
            "answer_completeness": average(("baseline_answer_score", "completeness")),
            "answer_factuality": average(("baseline_answer_score", "factuality")),
            "required_fact_coverage": average(("baseline_answer_score", "fact_coverage")),
            "provenance_accuracy": average(
                ("baseline_answer_score", "provenance_accuracy"), provenance_rows
            ),
            "retrieval_pass_rate": average(("baseline_retrieval_pass",)),
            "context_pass_rate": average(("baseline_context_pass",)),
            "context_tokens": baseline_tokens,
            "latency_ms": average(("baseline_latency_ms",)),
        },
        "redstone": {
            "answer_accuracy": redstone_accuracy,
            "answer_completeness": average(("redstone_answer_score", "completeness")),
            "answer_factuality": average(("redstone_answer_score", "factuality")),
            "required_fact_coverage": average(("redstone_answer_score", "fact_coverage")),
            "provenance_accuracy": average(
                ("redstone_answer_score", "provenance_accuracy"), provenance_rows
            ),
            "retrieval_recall": average(("retrieval_recall",)),
            "retrieval_precision": average(("retrieval_precision",)),
            "retrieval_f1": average(("retrieval_f1",)),
            "requirement_coverage": average(("requirement_coverage",)),
            "retrieval_pass_rate": average(("redstone_retrieval_pass",)),
            "context_pass_rate": average(("redstone_context_pass",)),
            "context_tokens": redstone_tokens,
            "latency_ms": average(("redstone_latency_ms",)),
        },
        "answer_accuracy_improvement": redstone_accuracy - baseline_accuracy,
        "context_reduction": (
            (baseline_tokens - redstone_tokens) / baseline_tokens if baseline_tokens else 0.0
        ),
        "category_accuracy": category_accuracy,
        "baseline_failures": dict(Counter(row["baseline_failure"] for row in rows if row["baseline_failure"])),
        "redstone_failures": dict(Counter(row["redstone_failure"] for row in rows if row["redstone_failure"])),
        "questions": rows,
    }
