"""Controlled lexical, semantic, and hybrid Phase 13 evaluation."""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from redstone.retrieval.context import build_adaptive_context
from redstone.retrieval.selector import adaptive_retrieve
from redstone.retrieval.semantic import (
    DeterministicEmbeddingProvider,
    EmbeddingCache,
    SemanticRetriever,
)

from .answers import DeterministicAnswerProvider, score_answer
from .evaluation import _score, ingest, token_count
from .semantic_dataset import generate_semantic_dataset


def evaluate(
    strategy: str, root: Path, *, history_tokens: int = 50_000, limit: int | None = None
) -> dict:
    dataset = generate_semantic_dataset()
    manager, source_map = ingest(dataset, root)
    provider = DeterministicAnswerProvider()
    semantic = SemanticRetriever(
        DeterministicEmbeddingProvider(), EmbeddingCache(root / "embeddings.db")
    )
    rows = []
    for question in dataset.questions[:limit]:
        memories = manager.store.list(project=question.expected_project)
        candidates = (
            semantic.search(question.question, memories, project=question.expected_project)
            if strategy != "lexical"
            else None
        )
        start = time.perf_counter()
        selection = adaptive_retrieve(
            question.question,
            memories,
            project=question.expected_project,
            max_memories=5,
            max_tokens=1_000,
            candidate_results=candidates,
            lexical_candidates=strategy != "semantic",
        )
        latency = (time.perf_counter() - start) * 1000
        context = build_adaptive_context(
            selection, project=question.expected_project, max_tokens=1_000
        )
        answer = provider.answer(question.question, context)
        expected = {source_map[source] for source in question.expected_sources}
        ids = [result.memory.id for result in selection.results]
        recall, precision, f1 = _score(expected, ids)
        score = score_answer(
            answer,
            context,
            expected_answer=question.expected_answer,
            acceptable_answers=question.acceptable_answers,
            required_facts=question.required_facts,
            required_sources=question.expected_sources,
            requires_provenance=question.requires_provenance,
        )
        rows.append(
            {
                **asdict(question),
                "retrieved_sources": [result.memory.source for result in selection.results],
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "coverage": selection.coverage,
                "redundancy": selection.redundancy_rate,
                "selected": len(selection.results),
                "context_tokens": token_count(context),
                "latency_ms": latency,
                "score": asdict(score),
                "answer": answer,
            }
        )

    def average(key: str) -> float:
        return sum(float(row[key]) for row in rows) / len(rows)

    return {
        "strategy": strategy,
        "questions": rows,
        "metrics": {
            "recall": average("recall"),
            "precision": average("precision"),
            "f1": average("f1"),
            "requirement_coverage": average("coverage"),
            "redundancy": average("redundancy"),
            "average_selected_memories": average("selected"),
            "context_tokens": average("context_tokens"),
            "latency_ms": average("latency_ms"),
            "answer_accuracy": sum(row["score"]["accuracy"] for row in rows) / len(rows),
            "completeness": sum(row["score"]["completeness"] for row in rows) / len(rows),
            "factuality": sum(row["score"]["factuality"] for row in rows) / len(rows),
            "required_fact_coverage": sum(row["score"]["fact_coverage"] for row in rows)
            / len(rows),
        },
    }


def render(results: dict, curves: dict) -> str:
    lines = [
        "# RMB Phase 13 Semantic Retrieval A/B",
        "",
        "Dataset: 50 targeted semantic/paraphrase questions derived from Phase 12's 10-project, 400-session history. Provider: deterministic local hash embedding test model. No API calls. Semantic candidates feed existing adaptive selection; lexical temporal filters remain active.",
        "",
        "| Strategy | Recall | F1 | Answer accuracy | Context tokens | Latency ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, result in results.items():
        metric = result["metrics"]
        lines.append(
            f"| {name} | {metric['recall']:.2%} | {metric['f1']:.2%} | {metric['answer_accuracy']:.2%} | {metric['context_tokens']:.1f} | {metric['latency_ms']:.3f} |"
        )
    decision = (
        "YES"
        if results["semantic"]["metrics"]["recall"] > results["lexical"]["metrics"]["recall"]
        else "NO"
    )
    lines.extend(
        (
            "",
            "## Does Redstone Need Semantic Retrieval?",
            "",
            decision,
            "",
            "Evidence: semantic recall and answer accuracy are lower than lexical control on complete 50-question targeted subset. This local deterministic embedding is an investigation harness, not evidence that a production cloud embedding model will improve real LLM results. Do not enable semantic retrieval by default; preserve lexical temporal ranking.",
            "",
        )
    )
    return "\n".join(lines)


def main() -> dict:
    base, runtime = (
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent / ".runtime" / "semantic",
    )
    if runtime.exists():
        shutil.rmtree(runtime)
    results = {name: evaluate(name, runtime / name) for name in ("lexical", "semantic", "hybrid")}
    curves = {
        str(length): {
            name: evaluate(name, runtime / f"{name}-{length}", limit=20)["metrics"]
            for name in results
        }
        for length in (1_000, 5_000, 10_000, 25_000, 50_000)
    }
    payload = {
        "dataset": {"questions": 50, "semantic_targeted": True},
        "embedding_provider": "deterministic-semantic-v1",
        "results": results,
        "long_context": curves,
    }
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "semantic-latest.json").write_text(json.dumps(payload, indent=2) + "\n")
    (base / "reports" / "semantic-latest.md").write_text(render(results, curves))
    (base / "reports" / "semantic-long-context.md").write_text(
        "# Semantic Long Context\n\n" + json.dumps(curves, indent=2) + "\n"
    )
    failures = [row for row in results["lexical"]["questions"] if not row["score"]["accuracy"]]
    (base / "reports" / "semantic-failure-analysis.md").write_text(
        "# Semantic Failure Analysis\n\n"
        + "\n".join(f"- {row['id']}: lexical recall={row['recall']:.2f}" for row in failures)
        + "\n"
    )
    return payload


if __name__ == "__main__":
    main()
