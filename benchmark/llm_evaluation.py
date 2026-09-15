"""Phase 12 provider-neutral long-context evaluation."""

from __future__ import annotations

import hashlib
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from redstone.retrieval.context import build_adaptive_context

from .answer_evaluation import _context_has_ground_truth, attribute_failure
from .answers import AnswerProvider, score_answer
from .dataset import Dataset
from .evaluation import _score, ingest, token_count

HISTORY_LENGTHS = (1_000, 5_000, 10_000, 25_000, 50_000)
BENCHMARK_VERSION = "phase12-authored-v1"


def _history(dataset: Dataset, project: str, tokens: int) -> str:
    lines = [
        f"[source={item.id}] {item.content}"
        for item in dataset.conversations
        if item.project == project
    ]
    text = "\n".join(lines)
    filler = 0
    while token_count(text) < tokens:
        filler += 1
        lines.append(
            f"[source={project}-long-noise-{filler:05d}] Routine discussion {filler}: "
            "database tutorial vocabulary appeared; no project decision changed."
        )
        text = "\n".join(lines)
    return text


def _tail(text: str, budget: int) -> str:
    lines, used = [], 0
    for line in reversed(text.splitlines()):
        size = token_count(line)
        if used + size > budget:
            break
        lines.append(line)
        used += size
    return "\n".join(reversed(lines))


def _prompt_tokens(question: str, context: str) -> int:
    return token_count(question) + token_count(context)


def _metrics(rows: list[dict[str, Any]], prefix: str) -> dict[str, float]:
    def avg(path: tuple[str, ...], subset: list[dict[str, Any]] | None = None) -> float:
        values = []
        for row in subset if subset is not None else rows:
            value: Any = row
            for key in path:
                value = value[key]
            if value is not None:
                values.append(float(value))
        return sum(values) / len(values) if values else 0.0

    scores = f"{prefix}_score"
    provenance = [row for row in rows if row["requires_provenance"]]
    temporal = [row for row in rows if row["category"] == "temporal"]
    return {
        "answer_accuracy": avg((scores, "accuracy")),
        "completeness": avg((scores, "completeness")),
        "factuality": avg((scores, "factuality")),
        "relevance": avg((scores, "accuracy")),
        "required_fact_coverage": avg((scores, "fact_coverage")),
        "provenance_accuracy": avg((scores, "accuracy"), provenance) if provenance else 0.0,
        "temporal_accuracy": (
            sum(float(row[scores]["accuracy"]) for row in temporal) / len(temporal)
            if temporal
            else 0.0
        ),
        "hallucination_rate": 1 - avg((scores, "factuality")),
        "context_tokens": avg((f"{prefix}_context_tokens",)),
        "prompt_tokens": avg((f"{prefix}_prompt_tokens",)),
        "output_tokens": avg((f"{prefix}_output_tokens",)),
        "total_tokens": avg((f"{prefix}_total_tokens",)),
        "latency_ms": avg((f"{prefix}_latency_ms",)),
    }


def _blind_labels(question_id: str) -> tuple[str, str]:
    return (
        ("A", "B") if int(hashlib.sha256(question_id.encode()).hexdigest(), 16) % 2 else ("B", "A")
    )


def evaluate_llm(
    dataset: Dataset,
    root: Path,
    provider: AnswerProvider,
    *,
    history_tokens: int = 50_000,
    budget_tokens: int = 1_000,
    full_history: bool = False,
    max_questions: int | None = None,
    judge: bool = False,
) -> dict[str, Any]:
    """Compare same provider on recent history versus retrieved context."""
    manager, source_map = ingest(dataset, root)
    rows: list[dict[str, Any]] = []
    histories: dict[str, str] = {}
    for question in dataset.questions[:max_questions]:
        project = question.expected_project or "atlas"
        if project not in histories:
            histories[project] = _history(dataset, project, history_tokens)
        history = histories[project]
        baseline_context = history if full_history else _tail(history, budget_tokens)
        selection = manager.retrieve_adaptive(
            question.question,
            project=question.expected_project,
            max_memories=5,
            max_tokens=budget_tokens,
        )
        redstone_context = build_adaptive_context(
            selection, project=question.expected_project, max_tokens=budget_tokens
        )
        required_sources = tuple(question.expected_sources)
        expected_ids = {source_map[source] for source in required_sources}
        start = time.perf_counter()
        baseline_answer = provider.answer(question.question, baseline_context)
        baseline_latency = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        redstone_answer = provider.answer(question.question, redstone_context)
        redstone_latency = (time.perf_counter() - start) * 1000
        baseline_score = score_answer(
            baseline_answer,
            baseline_context,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            required_facts=question.required_facts,
            required_sources=required_sources,
            requires_provenance=question.requires_provenance,
        )
        redstone_score = score_answer(
            redstone_answer,
            redstone_context,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            required_facts=question.required_facts,
            required_sources=required_sources,
            requires_provenance=question.requires_provenance,
        )
        retrieval_ids = [result.memory.id for result in selection.results]
        unsupported = question.category == "unsupported"
        baseline_context_ok = unsupported or _context_has_ground_truth(
            baseline_context,
            question.required_facts,
            required_sources,
            question.requires_provenance,
        )
        redstone_context_ok = unsupported or _context_has_ground_truth(
            redstone_context,
            question.required_facts,
            required_sources,
            question.requires_provenance,
        )
        labels = _blind_labels(question.id)
        judge_scores = None
        judge_method = getattr(provider, "judge", None)
        if judge and callable(judge_method):
            candidates = {labels[0]: baseline_answer, labels[1]: redstone_answer}
            judge_scores = {
                label: judge_method(question.question, question.expected_answer, answer)
                for label, answer in candidates.items()
            }
        rows.append(
            {
                **asdict(question),
                "history_tokens": token_count(history),
                "comparison": "full_history" if full_history else "equal_budget",
                "baseline_context": baseline_context,
                "redstone_context": redstone_context,
                "baseline_answer": baseline_answer,
                "redstone_answer": redstone_answer,
                "blind_candidate_labels": {"baseline": labels[0], "redstone": labels[1]},
                "blind_judge_scores": judge_scores,
                "baseline_score": asdict(baseline_score),
                "redstone_score": asdict(redstone_score),
                "baseline_context_tokens": token_count(baseline_context),
                "redstone_context_tokens": token_count(redstone_context),
                "baseline_prompt_tokens": _prompt_tokens(question.question, baseline_context),
                "redstone_prompt_tokens": _prompt_tokens(question.question, redstone_context),
                "baseline_output_tokens": token_count(baseline_answer),
                "redstone_output_tokens": token_count(redstone_answer),
                "baseline_total_tokens": _prompt_tokens(question.question, baseline_context)
                + token_count(baseline_answer),
                "redstone_total_tokens": _prompt_tokens(question.question, redstone_context)
                + token_count(redstone_answer),
                "baseline_latency_ms": baseline_latency,
                "redstone_latency_ms": redstone_latency,
                "retrieved_memory_ids": retrieval_ids,
                "retrieved_sources": [item.memory.source for item in selection.results],
                "retrieval_recall": _score(expected_ids, retrieval_ids)[0] if expected_ids else 1.0,
                "baseline_context_pass": baseline_context_ok,
                "redstone_context_pass": redstone_context_ok,
                "baseline_failure": attribute_failure(
                    baseline_context_ok, baseline_context_ok, bool(baseline_score.accuracy)
                ),
                "redstone_failure": attribute_failure(
                    bool(expected_ids <= set(retrieval_ids) or not expected_ids),
                    redstone_context_ok,
                    bool(redstone_score.accuracy),
                ),
            }
        )
    baseline, redstone = _metrics(rows, "baseline"), _metrics(rows, "redstone")
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset": {
            "projects": len(dataset.projects),
            "sessions": len(dataset.conversations),
            "important_facts": len(dataset.conversations),
            "questions": len(rows),
            "synthetic": True,
        },
        "configuration": {
            "provider": provider.metadata(),
            "history_tokens": history_tokens,
            "budget_tokens": budget_tokens,
            "comparison": "full_history" if full_history else "equal_budget",
            "baseline_input": "entire available history"
            if full_history
            else "most recent history within equal budget",
            "redstone_input": "adaptive context from same full history within equal budget",
            "blind_llm_judge": judge and callable(getattr(provider, "judge", None)),
        },
        "baseline": baseline,
        "redstone": redstone,
        "context_reduction": (baseline["context_tokens"] - redstone["context_tokens"])
        / baseline["context_tokens"]
        if baseline["context_tokens"]
        else 0.0,
        "failure_attribution": {
            stage: sum(
                row[f"{side}_failure"] == stage for row in rows for side in ("baseline", "redstone")
            )
            for stage in (
                "retrieval_failure",
                "context_failure",
                "answer_generation_failure",
                "evaluation_failure",
                "temporal_failure",
                "provenance_failure",
                "uncertainty_failure",
            )
        },
        "questions": rows,
    }


def summarize_runs(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    metrics = (
        "answer_accuracy",
        "completeness",
        "factuality",
        "context_tokens",
        "total_tokens",
        "latency_ms",
    )
    return {
        side: {
            metric: {
                "mean": statistics.mean([run[side][metric] for run in results]),
                "minimum": min(run[side][metric] for run in results),
                "maximum": max(run[side][metric] for run in results),
                "stddev": statistics.pstdev([run[side][metric] for run in results]),
            }
            for metric in metrics
        }
        for side in ("baseline", "redstone")
    }
