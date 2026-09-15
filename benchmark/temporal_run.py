"""Run Phase 15 deterministic temporal/conflict composition benchmark."""

from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from pathlib import Path

from redstone.reasoning.temporal import build_temporal_context

from .evaluation import _score, ingest, token_count
from .temporal_dataset import generate_temporal_dataset


def _composition_ids(composition, category: str) -> set[str]:
    if category == "current":
        return set(composition.current_memory_ids)
    if category in {"date", "partial"}:
        return set(composition.effective_memory_ids)
    if category == "unresolved":
        return {
            item
            for conflict in composition.conflicts
            if conflict.status == "unresolved"
            for item in conflict.candidate_ids
        }
    if category == "resolved":
        return {
            item
            for conflict in composition.conflicts
            if conflict.status == "resolved"
            for item in conflict.candidate_ids
        }
    return {entry.memory_id for entry in composition.timeline}


def evaluate(root: Path) -> dict:
    dataset = generate_temporal_dataset()
    manager, source_map = ingest(dataset, root)
    rows = []
    for question in dataset.questions:
        expected = {source_map[source] for source in question.expected_sources}
        start = time.perf_counter()
        baseline = manager.retrieve_adaptive(
            question.question, project=question.expected_project, max_memories=5, max_tokens=500
        )
        retrieval_ms = (time.perf_counter() - start) * 1_000
        baseline_ids = [result.memory.id for result in baseline.results]
        baseline_recall, baseline_precision, baseline_f1 = _score(expected, baseline_ids)
        start = time.perf_counter()
        composition = manager.compose_temporal(question.question, project=question.expected_project)
        composition_ms = (time.perf_counter() - start) * 1_000
        composed_ids = _composition_ids(composition, question.category)
        accuracy = float(expected <= composed_ids)
        if question.category == "context":
            accuracy = float(not composition.conflicts)
        context = build_temporal_context(composition)
        failure = None
        if not accuracy:
            failure = (
                "retrieval_failure" if baseline_recall == 0 else "timeline_composition_failure"
            )
            if question.category == "unresolved":
                failure = "conflict_classification_failure"
            if question.category in {"date", "partial"}:
                failure = "state_derivation_failure"
        rows.append(
            {
                "id": question.id,
                "category": question.category,
                "expected_sources": question.expected_sources,
                "retrieved_ids": baseline_ids,
                "baseline_recall": baseline_recall,
                "baseline_precision": baseline_precision,
                "baseline_f1": baseline_f1,
                "composition_ids": sorted(composed_ids),
                "accuracy": accuracy,
                "provenance": float(all(entry.source for entry in composition.timeline)),
                "context_sufficient": float(
                    expected <= {entry.memory_id for entry in composition.timeline}
                ),
                "context_tokens": token_count(context),
                "redundancy": baseline.redundancy_rate,
                "retrieval_ms": retrieval_ms,
                "composition_ms": composition_ms,
                "total_ms": retrieval_ms + composition_ms,
                "failure": failure,
            }
        )

    def average(key: str, category: str | None = None) -> float:
        selected = [row for row in rows if category is None or row["category"] == category]
        return sum(row[key] for row in selected) / len(selected) if selected else 0.0

    categories = sorted({row["category"] for row in rows})
    return {
        "dataset": {
            "projects": len(dataset.projects),
            "memories": len(dataset.conversations),
            "scenarios": len(dataset.questions),
            "questions": len(dataset.questions),
            "categories": categories,
        },
        "phase14_baseline": {"timeline_conflict_accuracy": 0.5},
        "phase15": {
            "overall_accuracy": average("accuracy"),
            "timeline_accuracy": average("accuracy", "timeline"),
            "current_state_accuracy": average("accuracy", "current"),
            "historical_state_accuracy": average("accuracy", "historical"),
            "conflict_accuracy": (
                average("accuracy", "resolved")
                + average("accuracy", "unresolved")
                + average("accuracy", "context")
            )
            / 3,
            "decision_history_accuracy": average("accuracy", "decision"),
            "retrieval_recall": average("baseline_recall"),
            "retrieval_precision": average("baseline_precision"),
            "retrieval_f1": average("baseline_f1"),
            "context_sufficiency": average("context_sufficient"),
            "provenance_accuracy": average("provenance"),
            "context_tokens": average("context_tokens"),
            "redundancy": average("redundancy"),
            "retrieval_latency_ms": average("retrieval_ms"),
            "composition_latency_ms": average("composition_ms"),
            "end_to_end_latency_ms": average("total_ms"),
        },
        "category_accuracy": {category: average("accuracy", category) for category in categories},
        "failures": dict(Counter(row["failure"] for row in rows if row["failure"])),
        "questions": rows,
    }


def render(results: dict) -> str:
    metric = results["phase15"]
    categories = "\n".join(
        f"- {name}: {value:.2%}" for name, value in results["category_accuracy"].items()
    )
    return f"""# RMB Phase 15 Temporal and Conflict Composition

Root cause: Phase 14 adaptive selection stopped timelines after two memories once abstract requirements were covered, and duplicate suppression rejected the second unresolved-conflict candidate. Phase 15 keeps complete bounded chains and contradiction candidates, then composes structured state with provenance.

Dataset: {results["dataset"]["projects"]} projects, {results["dataset"]["memories"]} memories, {results["dataset"]["scenarios"]} authored scenarios/questions.

| Metric | Phase 14 | Phase 15 |
| --- | ---: | ---: |
| Timeline/conflict accuracy | 50.00% | {((metric["timeline_accuracy"] + metric["conflict_accuracy"]) / 2):.2%} |
| Current-state accuracy | not measured | {metric["current_state_accuracy"]:.2%} |
| Historical-state accuracy | not measured | {metric["historical_state_accuracy"]:.2%} |
| Conflict accuracy | not measured | {metric["conflict_accuracy"]:.2%} |
| Decision-history accuracy | not measured | {metric["decision_history_accuracy"]:.2%} |
| Retrieval recall | 80.00% | {metric["retrieval_recall"]:.2%} |
| Retrieval precision | 90.00% | {metric["retrieval_precision"]:.2%} |
| Retrieval F1 | 83.33% | {metric["retrieval_f1"]:.2%} |
| Context sufficiency | not measured | {metric["context_sufficiency"]:.2%} |
| Provenance | 100.00% | {metric["provenance_accuracy"]:.2%} |
| Context tokens | 116.7 | {metric["context_tokens"]:.1f} |
| End-to-end latency | not comparable | {metric["end_to_end_latency_ms"]:.3f} ms |

## Categories

{categories}

## Limitations

Deterministic authored workload and reasoning. No LLM composition, embeddings, or universal temporal-reasoning claim. Month-only date queries assume one calendar year. Unlinked ambiguous memories remain uncertain. Content subject extraction is conservative and cannot resolve every natural-language relation.
"""


def main() -> dict:
    base, runtime = (
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent / ".runtime" / "temporal",
    )
    if runtime.exists():
        shutil.rmtree(runtime)
    results = evaluate(runtime)
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "temporal-latest.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    (base / "reports" / "temporal-latest.md").write_text(render(results))
    failures = [row for row in results["questions"] if row["failure"]]
    lines = ["# Temporal/Conflict Failure Analysis", ""] + (
        [f"- {row['id']}: {row['failure']}" for row in failures] or ["No composition failures."]
    )
    (base / "reports" / "temporal-conflict-failure-analysis.md").write_text("\n".join(lines) + "\n")
    return results


if __name__ == "__main__":
    main()
