"""Run Phase 12 offline or configured real-LLM memory evaluation."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .answers import AnswerProvider, provider_from_environment
from .llm_dataset import generate_llm_dataset
from .llm_evaluation import HISTORY_LENGTHS, evaluate_llm, summarize_runs


def _table(results: dict) -> str:
    baseline, redstone = results["baseline"], results["redstone"]
    labels = (
        ("Answer accuracy", "answer_accuracy"),
        ("Completeness", "completeness"),
        ("Factuality", "factuality"),
        ("Relevance", "relevance"),
        ("Required-fact coverage", "required_fact_coverage"),
        ("Provenance accuracy", "provenance_accuracy"),
        ("Temporal accuracy", "temporal_accuracy"),
        ("Hallucination rate", "hallucination_rate"),
        ("Context tokens", "context_tokens"),
        ("Total tokens", "total_tokens"),
        ("Latency ms", "latency_ms"),
    )
    lines = ["| Metric | Baseline | Redstone |", "| --- | ---: | ---: |"]
    for label, key in labels:
        suffix = "" if key in {"context_tokens", "total_tokens", "latency_ms"} else "%"
        scale = 1 if suffix == "" else 100
        lines.append(
            f"| {label} | {baseline[key] * scale:.2f}{suffix} | {redstone[key] * scale:.2f}{suffix} |"
        )
    return "\n".join(lines)


def render_report(results: dict, full_history: dict, curves: dict[str, dict], repeats: dict) -> str:
    config, dataset = results["configuration"], results["dataset"]
    return f"""# RMB Phase 12 LLM Memory Evaluation

Dataset: {dataset["projects"]} synthetic projects, {dataset["sessions"]} sessions, {dataset["important_facts"]} authored facts, {dataset["questions"]} questions. Dataset version: `{results["benchmark_version"]}`. Run timestamp: `{datetime.now(UTC).isoformat()}`.

Provider settings (no credentials): `{config["provider"]}`.

## Method

Equal-budget: baseline receives most recent history limited to {config["budget_tokens"]} estimated tokens. Redstone receives adaptive retrieval context from same complete project history, also limited to {config["budget_tokens"]} estimated tokens. Same provider answers both paths. Expected facts never enter provider input.

Full-history ablation: baseline receives full {full_history["configuration"]["history_tokens"]} token history; Redstone remains retrieval-bounded. This is separate from equal-budget results.

Deterministic layer scores normalized required facts, grounding against supplied context, provenance, temporal questions, and unsupported answers. Blind candidate labels are randomized per question and retained only as mappings. An external LLM judge is optional and not run by offline deterministic mode; no judge result is presented as LLM judgment.

## Equal-Budget Results

{_table(results)}

Context reduction: {results["context_reduction"]:.2%}.

## Full-History Ablation

{_table(full_history)}

## Repeats

Configured repeated-run summary: `{repeats}`. Deterministic provider has no sampling variance; real providers should use `--runs 3` on a declared subset before interpreting variance. No statistical-significance claim is made.

## Limitations

Synthetic authored data; estimated token counts; deterministic scorer cannot assess arbitrary prose quality. A real provider run requires explicit environment credentials and may have provider cost, latency, context-window, and version changes. No embeddings, vector database, reranker, cloud memory, or memory consolidation is used.
"""


def render_long_context(curves: dict[str, dict]) -> str:
    lines = [
        "# RMB Phase 12 Long-Context Curves",
        "",
        "Curves use equal-budget 1,000-token inputs. Each length uses same first 20 complete-population questions to limit repeated-run cost; primary 50K results evaluate all questions.",
        "",
        "| History Length | Baseline Accuracy | Redstone Accuracy | Baseline Context | Redstone Context |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for length, result in curves.items():
        lines.append(
            f"| {int(length) // 1000}K | {result['baseline']['answer_accuracy']:.2%} | {result['redstone']['answer_accuracy']:.2%} | {result['baseline']['context_tokens']:.1f} | {result['redstone']['context_tokens']:.1f} |"
        )
    return "\n".join(lines) + "\n"


def render_failures(results: dict) -> str:
    lines = ["# RMB Phase 12 Failure Analysis", ""]
    for row in results["questions"]:
        if not row["baseline_failure"] and not row["redstone_failure"]:
            continue
        lines.extend(
            (
                f"## {row['id']}",
                "",
                f"Baseline root: {row['baseline_failure'] or 'none'}",
                f"Redstone root: {row['redstone_failure'] or 'none'}",
                f"Retrieved sources: {', '.join(row['retrieved_sources']) or 'none'}",
                "",
            )
        )
    if len(lines) == 2:
        lines.append("No scored failures.")
    return "\n".join(lines) + "\n"


def main(
    *,
    provider_name: str | None = None,
    runs: int = 1,
    max_questions: int | None = None,
    judge: bool = False,
) -> dict:
    provider: AnswerProvider = provider_from_environment(provider_name)
    base = Path(__file__).resolve().parent
    runtime = base / ".runtime" / "llm"
    if runtime.exists():
        shutil.rmtree(runtime)
    dataset = generate_llm_dataset()
    equal_runs = [
        evaluate_llm(
            dataset, runtime / f"equal-{index}", provider, max_questions=max_questions, judge=judge
        )
        for index in range(runs)
    ]
    full_history = evaluate_llm(
        dataset,
        runtime / "full-history",
        provider,
        full_history=True,
        max_questions=max_questions,
        judge=judge,
    )
    curve_questions = min(max_questions or 20, 20)
    curves = {
        str(length): evaluate_llm(
            dataset,
            runtime / f"curve-{length}",
            provider,
            history_tokens=length,
            max_questions=curve_questions,
        )
        for length in HISTORY_LENGTHS
    }
    results = equal_runs[0]
    results["run_summary"] = summarize_runs(equal_runs)
    results["full_history_ablation"] = {
        key: value for key, value in full_history.items() if key != "questions"
    }
    results["long_context_curves"] = {
        key: {
            "baseline": value["baseline"],
            "redstone": value["redstone"],
            "question_count": value["dataset"]["questions"],
        }
        for key, value in curves.items()
    }
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "llm-latest.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (base / "reports" / "llm-latest.md").write_text(
        render_report(results, full_history, curves, results["run_summary"]), encoding="utf-8"
    )
    (base / "reports" / "llm-long-context.md").write_text(
        render_long_context(curves), encoding="utf-8"
    )
    (base / "reports" / "llm-failure-analysis.md").write_text(
        render_failures(results), encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    main()
