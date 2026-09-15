"""Render answer-level RMB reports."""

from __future__ import annotations


def render_answer_report(results: dict) -> str:
    baseline = results["baseline"]
    redstone = results["redstone"]
    dataset = results["dataset"]
    categories = "\n".join(
        f"- {name}: baseline {scores['baseline']:.2%}; Redstone {scores['redstone']:.2%}"
        for name, scores in results["category_accuracy"].items()
    )
    baseline_failures = ", ".join(
        f"{name}={count}" for name, count in results["baseline_failures"].items()
    ) or "none"
    redstone_failures = ", ".join(
        f"{name}={count}" for name, count in results["redstone_failures"].items()
    ) or "none"
    return f"""# RMB Answer-Level Benchmark

Dataset: {dataset['projects']} projects, {dataset['sessions']} sessions, {dataset['questions']} questions.

Provider: `{results['configuration']['provider']}`. This deterministic extractive provider tests the pipeline without external APIs; it does not measure general LLM quality.

Both paths receive at most {results['configuration']['context_budget_tokens']} context tokens. Baseline receives the most recent project history fitting that budget. Redstone receives adaptive context retrieved from the same history.

## Baseline

- Answer accuracy: {baseline['answer_accuracy']:.2%}
- Completeness: {baseline['answer_completeness']:.2%}
- Factuality: {baseline['answer_factuality']:.2%}
- Required-fact coverage: {baseline['required_fact_coverage']:.2%}
- Provenance accuracy: {baseline['provenance_accuracy']:.2%}
- Context pass rate: {baseline['context_pass_rate']:.2%}
- Context: {baseline['context_tokens']:.1f} tokens
- Pipeline latency: {baseline['latency_ms']:.3f} ms/question

## Redstone

- Answer accuracy: {redstone['answer_accuracy']:.2%}
- Completeness: {redstone['answer_completeness']:.2%}
- Factuality: {redstone['answer_factuality']:.2%}
- Required-fact coverage: {redstone['required_fact_coverage']:.2%}
- Provenance accuracy: {redstone['provenance_accuracy']:.2%}
- Retrieval recall: {redstone['retrieval_recall']:.2%}
- Retrieval precision: {redstone['retrieval_precision']:.2%}
- Retrieval F1: {redstone['retrieval_f1']:.2%}
- Requirement coverage: {redstone['requirement_coverage']:.2%}
- Context pass rate: {redstone['context_pass_rate']:.2%}
- Context: {redstone['context_tokens']:.1f} tokens
- Pipeline latency: {redstone['latency_ms']:.3f} ms/question

Answer accuracy difference: {results['answer_accuracy_improvement']:+.2%}
Context reduction: {results['context_reduction']:.2%}

Stage attributions:
- Baseline: {baseline_failures}
- Redstone: {redstone_failures}

## Category Accuracy

{categories}

## Interpretation

RMB is synthetic. Results measure deterministic extractive answer generation over authored workloads, not open-ended LLM reasoning or general AI-memory quality.
"""


def render_answer_failures(results: dict) -> str:
    lines = ["# RMB Answer-Level Stage Attribution", ""]
    for row in results["questions"]:
        if not row["baseline_failure"] and not row["redstone_failure"]:
            continue
        lines.extend(
            (
                f"## {row['id']}",
                "",
                f"Question: {row['question']}",
                f"Required facts: {', '.join(row['required_facts'])}",
                f"Baseline: retrieval={'PASS' if row['baseline_retrieval_pass'] else 'FAIL'}, context={'PASS' if row['baseline_context_pass'] else 'FAIL'}, answer={'PASS' if row['baseline_answer_score']['accuracy'] else 'FAIL'}; attribution={row['baseline_failure'] or 'none'}",
                f"Redstone: retrieval={'PASS' if row['redstone_retrieval_pass'] else 'FAIL'}, context={'PASS' if row['redstone_context_pass'] else 'FAIL'}, answer={'PASS' if row['redstone_answer_score']['accuracy'] else 'FAIL'}; attribution={row['redstone_failure'] or 'none'}",
                "",
            )
        )
    if len(lines) == 2:
        lines.append("No stage failures.")
    return "\n".join(lines) + "\n"
