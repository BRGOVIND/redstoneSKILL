"""Run and report deterministic Phase 11 robustness RMB."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .robustness_dataset import generate_robustness_dataset
from .robustness_evaluation import evaluate_robustness

FAILURE_LABELS = (
    "retrieval_failure",
    "context_failure",
    "generation_failure",
    "evaluation_failure",
    "uncertainty_failure",
    "temporal_failure",
    "provenance_failure",
    "security_failure",
)


def render_report(results: dict) -> str:
    baseline, redstone, dataset = results["baseline"], results["redstone"], results["dataset"]
    categories = "\n".join(
        f"- {name}: {count}" for name, count in dataset["category_counts"].items()
    )
    failures = "\n".join(
        f"- {label}: {results['failures'].get(label, 0)}" for label in FAILURE_LABELS
    )
    return f"""# RMB Robustness Benchmark

Dataset: {dataset['projects']} projects, {dataset['sessions']} sessions, {dataset['stored_memories']} stored memories, {dataset['questions']} questions.

Version: `{dataset['version']}`. Provider: `{results['configuration']['provider']}`. Context budget: {results['configuration']['context_budget_tokens']} tokens. Maximum memories: {results['configuration']['max_memories']}.

Both paths use identical questions, answer provider, token budget, and scoring. Baseline receives recent history. Redstone receives adaptive context from the same authored history.

| Metric | Baseline | Redstone |
| --- | ---: | ---: |
| Answer accuracy | {baseline['answer_accuracy']:.2%} | {redstone['answer_accuracy']:.2%} |
| Completeness | {baseline['completeness']:.2%} | {redstone['completeness']:.2%} |
| Factuality | {baseline['factuality']:.2%} | {redstone['factuality']:.2%} |
| Retrieval recall | {baseline['retrieval_recall']:.2%} | {redstone['retrieval_recall']:.2%} |
| Retrieval precision | {baseline['retrieval_precision']:.2%} | {redstone['retrieval_precision']:.2%} |
| Retrieval F1 | {baseline['retrieval_f1']:.2%} | {redstone['retrieval_f1']:.2%} |
| Context sufficiency | {baseline['context_sufficiency']:.2%} | {redstone['context_sufficiency']:.2%} |
| Context reduction | 0.00% | {results['context_reduction']:.2%} |
| Provenance accuracy | {baseline['provenance_accuracy']:.2%} | {redstone['provenance_accuracy']:.2%} |
| Temporal accuracy | {baseline['temporal_accuracy']:.2%} | {redstone['temporal_accuracy']:.2%} |
| Contradiction accuracy | {baseline['contradiction_accuracy']:.2%} | {redstone['contradiction_accuracy']:.2%} |
| Entity accuracy | {baseline['entity_accuracy']:.2%} | {redstone['entity_accuracy']:.2%} |
| Unsupported-answer rate | {baseline['unsupported_answer_rate']:.2%} | {redstone['unsupported_answer_rate']:.2%} |
| Adversarial failure rate | {baseline['adversarial_failure_rate']:.2%} | {redstone['adversarial_failure_rate']:.2%} |
| Latency | {baseline['latency_ms']:.3f} ms | {redstone['latency_ms']:.3f} ms |

Additional Redstone metrics: exact accuracy {redstone['exact_accuracy']:.2%}; normalized accuracy {redstone['normalized_accuracy']:.2%}; required-fact accuracy {redstone['required_fact_accuracy']:.2%}; requirement coverage {redstone['requirement_coverage']:.2%}; false-positive rate {redstone['false_positive_rate']:.2%}; redundant retrieval {redstone['redundant_retrieval_rate']:.2%}; average selected memories {redstone['average_memories_selected']:.2f}; context {redstone['context_tokens']:.1f} tokens; hallucination {redstone['hallucination_rate']:.2%}; stale-memory errors {redstone['stale_memory_error_rate']:.2%}.

## Categories

{categories}

## Failure Attribution

{failures}

Memory mutations during answer generation: {results['memory_mutations_during_answers']}.

## Interpretation

This deterministic authored benchmark uses synthetic adversarial cases and an extractive provider. It does not evaluate open-ended LLM behavior or prove general memory-system superiority. Factuality is limited to authored ground truth.
"""


def render_failures(results: dict) -> str:
    lines = ["# RMB Robustness Failure Analysis", ""]
    failures = [row for row in results["questions"] if row["failure"]]
    if not failures:
        lines.append("No Redstone failures in this run.")
    for row in failures:
        lines.extend(
            (
                f"## {row['id']}",
                "",
                f"Question: {row['question']}",
                f"Root failure: {row['failure']}",
                f"Expected sources: {', '.join(row['expected_sources']) or 'none'}",
                f"Retrieved sources: {', '.join(row['retrieved_sources']) or 'none'}",
                f"Required facts: {', '.join(row['required_facts']) or 'none'}",
                f"Answer: {row['answer']}",
                "",
            )
        )
    baseline_examples = [row for row in results["questions"] if row["baseline_failure"]][:8]
    if baseline_examples:
        lines.extend(("## Representative Baseline Failures", ""))
        lines.extend(
            f"- {row['id']}: {row['baseline_failure']}" for row in baseline_examples
        )
    return "\n".join(lines) + "\n"


def main() -> dict:
    base = Path(__file__).resolve().parent
    runtime = base / ".runtime" / "robustness"
    if runtime.exists():
        shutil.rmtree(runtime)
    results = evaluate_robustness(generate_robustness_dataset(), runtime)
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "robustness-latest.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (base / "reports" / "robustness-latest.md").write_text(
        render_report(results),
        encoding="utf-8",
    )
    (base / "reports" / "robustness-failure-analysis.md").write_text(
        render_failures(results),
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    main()
