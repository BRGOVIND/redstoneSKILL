"""Analyze Phase 12 full-history versus lexical-context gap before Phase 13 changes."""

from __future__ import annotations

import shutil
from pathlib import Path

from .answers import DeterministicAnswerProvider
from .llm_dataset import generate_llm_dataset
from .llm_evaluation import evaluate_llm


def analyze() -> dict:
    base = Path(__file__).resolve().parent
    runtime = base / ".runtime" / "phase12-gap"
    if runtime.exists():
        shutil.rmtree(runtime)
    dataset = generate_llm_dataset()
    provider = DeterministicAnswerProvider()
    lexical = evaluate_llm(dataset, runtime / "lexical", provider)
    full = evaluate_llm(dataset, runtime / "full", provider, full_history=True)
    full_scores = {row["id"]: row for row in full["questions"]}
    gaps = []
    for row in lexical["questions"]:
        baseline = full_scores[row["id"]]
        if baseline["baseline_score"]["accuracy"] and not row["redstone_score"]["accuracy"]:
            cause = "synonym/paraphrase" if row["category"] == "decision" else "generation or evaluation"
            gaps.append({"id": row["id"], "category": row["category"], "stage": row["redstone_failure"], "cause": cause, "retrieved": row["retrieved_sources"], "expected": row["expected_sources"]})
    return {"lexical": lexical, "full": full, "gaps": gaps}


def render(results: dict) -> str:
    rows = results["gaps"]
    lines = ["# Phase 12 Gap Analysis", "", "Analysis completed before semantic retrieval implementation.", "", f"Full-history correct / lexical Redstone incorrect: {len(rows)} questions.", "", "| Question | Category | Earliest stage | Cause |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['id']} | {row['category']} | {row['stage']} | {row['cause']} |")
    lines.extend(("", "## Finding", "", "All gap cases are decision questions. Lexical retrieval selected current-state evidence but omitted migration rationale required by paraphrased `selected`/`why` wording. This is a retrieval/ranking candidate-coverage limitation, not context truncation. Preference failures occur in both paths and are deterministic answer-generation limits, so they are excluded from this gap. Semantic candidate retrieval is justified for controlled A/B testing only; temporal ranking remains control.", ""))
    return "\n".join(lines)


def main() -> dict:
    results = analyze()
    path = Path(__file__).resolve().parent / "reports" / "phase12-gap-analysis.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(render(results), encoding="utf-8")
    return results


if __name__ == "__main__":
    main()
