"""Run hard RMB and write reproducible reports."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from benchmark.answer_evaluation import evaluate_answers
from benchmark.answer_report import render_answer_failures, render_answer_report
from benchmark.dataset import generate_dataset
from benchmark.evaluation import evaluate
from benchmark.realworld_dataset import generate_realworld_dataset


def render_report(results: dict) -> str:
    baseline, redstone, adaptive, dataset = (
        results["baseline"],
        results["redstone"],
        results["adaptive"],
        results["dataset"],
    )
    relative = results["relative_improvement"]
    relative_text = "undefined (baseline zero)" if relative is None else f"{relative:+.2%}"
    categories = "\n".join(
        f"- {key}: {value:.2%}" for key, value in results["category_accuracy"].items()
    )
    adaptive_categories = "\n".join(
        f"- {key}: {value:.2%}" for key, value in results["adaptive_category_accuracy"].items()
    )
    failures = (
        "\n".join(f"- {key}: {value}" for key, value in results["failure_categories"].items())
        or "- none"
    )
    distances = "\n".join(
        f"- {key} conversations: {value:.2%}" for key, value in results["distance_accuracy"].items()
    )
    return f"""# RMB — Redstone Memory Benchmark

Dataset: {dataset["conversations"]} conversations, {dataset["projects"]} projects, {dataset["entities"]} entities, {dataset["questions"]} questions ({dataset["multi_memory_questions"]} multi-memory).

This is a deterministic synthetic retrieval workload. Results apply to this dataset and do not establish general AI-memory or model performance.

## Baseline

- Recall: {baseline["recall"]:.2%}
- Precision: {baseline["precision"]:.2%}
- F1: {baseline["f1"]:.2%}
- Context: {baseline["context_tokens"]:.1f} tokens

## Redstone Fixed top_k=1

- Recall: {redstone["recall"]:.2%}
- Precision: {redstone["precision"]:.2%}
- F1: {redstone["f1"]:.2%}
- Context: {redstone["context_tokens"]:.1f} tokens
- Retrieval latency: {redstone["latency_ms"]:.3f} ms/question

## Redstone Adaptive

- Recall: {adaptive["recall"]:.2%}
- Precision: {adaptive["precision"]:.2%}
- F1: {adaptive["f1"]:.2%}
- Single-memory accuracy: {adaptive["single_memory_accuracy"]:.2%}
- Multi-memory accuracy: {adaptive["multi_memory_accuracy"]:.2%}
- Requirement coverage: {adaptive["requirement_coverage"]:.2%}
- Average memories selected: {adaptive["average_memories_selected"]:.2f}
- Redundancy rate: {adaptive["redundancy_rate"]:.2%}
- Context: {adaptive["context_tokens"]:.1f} tokens
- Retrieval latency: {adaptive["latency_ms"]:.3f} ms/question

Fixed vs baseline absolute recall difference: {results["absolute_improvement"]:+.2%}
Fixed vs baseline relative recall improvement: {relative_text}
Fixed vs baseline context reduction: {results["context_reduction"]:.2%}
Adaptive vs fixed recall difference: {results["adaptive_absolute_improvement"]:+.2%}
Adaptive vs fixed context change: {results["adaptive_context_change"]:+.2%}

## Category Accuracy

{categories}

## Adaptive Category Accuracy

{adaptive_categories}

## Failure Categories

{failures}

## Recall by Distance

{distances}
"""


def render_failures(results: dict) -> str:
    sections = ["# RMB Failure Analysis", ""]
    for row in results["questions"]:
        if not row["failure_category"]:
            continue
        missing = sorted(set(row["expected_memory_ids"]) - set(row["adaptive_memory_ids"]))
        sections.extend(
            (
                f"## {row['id']}",
                "",
                f"Question: {row['question']}",
                f"Expected memory IDs: {', '.join(row['expected_memory_ids'])}",
                f"Retrieved memory IDs: {', '.join(row['adaptive_memory_ids']) or 'none'}",
                f"Missing: {', '.join(missing)}",
                f"Likely failure category: {row['failure_category']}",
                "",
            )
        )
    if len(sections) == 2:
        sections.append("No retrieval failures.")
    return "\n".join(sections) + "\n"


def main() -> None:
    base = Path(__file__).resolve().parent
    runtime = base / ".runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    curves = {
        str(top_k): evaluate(generate_dataset(), runtime / f"k{top_k}", top_k=top_k)
        for top_k in (1, 2, 3, 5, 10)
    }
    results = curves["1"]
    results["retrieval_curves"] = {
        key: {
            "recall": value["redstone"]["recall"],
            "precision": value["redstone"]["precision"],
            "f1": value["redstone"]["f1"],
            "context_tokens": value["redstone"]["context_tokens"],
        }
        for key, value in curves.items()
    }
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "latest.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (base / "reports" / "latest.md").write_text(render_report(results), encoding="utf-8")
    (base / "reports" / "failure-analysis.md").write_text(
        render_failures(results), encoding="utf-8"
    )
    answer_results = evaluate_answers(
        generate_realworld_dataset(),
        runtime / "answer-level",
    )
    (base / "results" / "answer-latest.json").write_text(
        json.dumps(answer_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (base / "reports" / "answer-latest.md").write_text(
        render_answer_report(answer_results),
        encoding="utf-8",
    )
    (base / "reports" / "answer-failure-analysis.md").write_text(
        render_answer_failures(answer_results),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
