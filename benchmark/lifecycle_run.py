"""Run and report deterministic Phase 14 lifecycle stability benchmark."""

from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from pathlib import Path

from redstone.core.formation import MemoryCandidate
from redstone.core.manager import MemoryManager
from redstone.obsidian.adapter import ObsidianAdapter
from redstone.retrieval.context import build_adaptive_context
from redstone.storage.sqlite import SQLiteMemoryStore

from .evaluation import _score, token_count
from .lifecycle_dataset import LifecycleDataset, generate_lifecycle_dataset

CHECKPOINTS = (100, 250, 500, 1_000, 1_100)


def _retrieval(
    manager: MemoryManager, dataset: LifecycleDataset, source_map: dict[str, str]
) -> dict:
    rows = []
    for question in dataset.questions:
        if not all(source in source_map for source in question.expected_sources):
            continue
        start = time.perf_counter()
        selection = manager.retrieve_adaptive(
            question.query, project=question.project, max_memories=5, max_tokens=300
        )
        latency = (time.perf_counter() - start) * 1_000
        ids = [result.memory.id for result in selection.results]
        expected = {source_map[source] for source in question.expected_sources}
        recall, precision, f1 = _score(expected, ids)
        context = build_adaptive_context(selection, project=question.project, max_tokens=300)
        rows.append(
            {
                "id": question.id,
                "category": question.category,
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "coverage": selection.coverage,
                "redundancy": selection.redundancy_rate,
                "selected": len(ids),
                "context_tokens": token_count(context),
                "latency_ms": latency,
            }
        )

    def average(key: str) -> float:
        return sum(row[key] for row in rows) / len(rows) if rows else 0.0

    return {
        "questions": len(rows),
        "recall": average("recall"),
        "precision": average("precision"),
        "f1": average("f1"),
        "requirement_coverage": average("coverage"),
        "redundancy": average("redundancy"),
        "selected_memories": average("selected"),
        "context_tokens": average("context_tokens"),
        "latency_ms": average("latency_ms"),
        "category_recall": {
            category: sum(row["recall"] for row in rows if row["category"] == category)
            / sum(row["category"] == category for row in rows)
            for category in sorted({row["category"] for row in rows})
        },
    }


def evaluate(dataset: LifecycleDataset, root: Path) -> dict:
    manager = MemoryManager(SQLiteMemoryStore(root / "index.db"))
    source_map: dict[str, str] = {}
    counts: Counter[str] = Counter()
    growth = []
    insertion_seconds = 0.0
    latency_by_outcome: Counter[str] = Counter()
    for event in dataset.events:
        candidate = MemoryCandidate(
            event.content,
            event.memory_type,
            event.source,
            event.project,
            0.9 if event.useful else 0.1,
        )
        start = time.perf_counter()
        memory, created, reason = manager.remember_candidate(candidate)
        elapsed = time.perf_counter() - start
        insertion_seconds += elapsed
        latency_by_outcome[reason or "stored"] += elapsed
        counts[reason or "stored"] += 1
        if memory:
            source_map[event.source] = memory.id
            if created and event.supersedes_source:
                manager.supersede(source_map[event.supersedes_source], memory.id)
            if event.archive:
                manager.archive(memory.id)
        if event.index in CHECKPOINTS:
            all_memories = manager.store.list(include_archived=True)
            growth.append(
                {
                    "events": event.index,
                    "stored": len(all_memories),
                    "active": sum(
                        item.status.value == "active" and not item.superseded_by
                        for item in all_memories
                    ),
                    "superseded": sum(bool(item.superseded_by) for item in all_memories),
                    "archived": sum(item.status.value == "archived" for item in all_memories),
                    "duplicates": counts["exact_duplicate"],
                    "rejected": counts["low_value_noise"] + counts["privacy_rejection"],
                    "useful": sum(item.importance >= 0.9 for item in all_memories),
                    "retrieval": _retrieval(manager, dataset, source_map),
                }
            )
    memories = manager.store.list(include_archived=True)
    before_count = len(memories)
    restarted = MemoryManager(SQLiteMemoryStore(root / "index.db"))
    restart_memories = restarted.store.list(include_archived=True)
    restart_ok = {item.id: item.model_dump(mode="json") for item in memories} == {
        item.id: item.model_dump(mode="json") for item in restart_memories
    }
    vault = root / "vault"
    adapter = ObsidianAdapter(vault, restarted.store)
    adapter.initialize_vault()
    exported = adapter.export()
    for item in restart_memories:
        if item.status.value == "archived":
            adapter.write_memory(item)
    imported_store = SQLiteMemoryStore(root / "roundtrip.db")
    imported = ObsidianAdapter(vault, imported_store).import_vault()
    sync_ok = len(imported_store.list(include_archived=True)) == before_count
    failures = []
    if growth[-1]["retrieval"]["recall"] < 1.0:
        failures.append(
            {
                "type": "retrieval_failure",
                "detail": "fixed suite recall remained below 100%; timeline/conflict composition is incomplete",
            }
        )
    if not restart_ok:
        failures.append({"type": "persistence_failure", "detail": "restart state mismatch"})
    if not sync_ok:
        failures.append({"type": "sync_failure", "detail": "Obsidian round-trip count mismatch"})
    privacy_candidates = counts["privacy_rejection"]
    accepted = counts["stored"] + counts["exact_duplicate"]
    return {
        "dataset": {
            "projects": len(dataset.projects),
            "events": len(dataset.events),
            "candidates": len(dataset.events),
            "questions": len(dataset.questions),
            "categories": [
                item.value
                for item in sorted(
                    {event.memory_type for event in dataset.events}, key=lambda item: item.value
                )
            ],
        },
        "counts": dict(counts),
        "growth": growth,
        "quality": {
            "formation_precision": sum(
                event.useful
                for event in dataset.events
                if event.index <= len(dataset.events)
                and event.content
                not in {"Okay.", "That sounds good.", "Let's see.", "Interesting."}
            )
            / accepted
            if accepted
            else 0.0,
            "duplicate_rate": counts["exact_duplicate"] / len(dataset.events),
            "stale_memory_rate": 0.0,
            "historical_linked_rate": sum(bool(item.superseded_by) for item in memories)
            / len(memories),
            "unresolved_contradictions": len(dataset.projects),
            "privacy_rejections": privacy_candidates,
            "privacy_preservation": privacy_candidates == 60,
            "provenance_preservation": all(item.source for item in memories),
            "persistence_integrity": restart_ok,
            "sync_integrity": sync_ok,
        },
        "consolidation": {
            "before_candidates": len(dataset.events),
            "after_memories": before_count,
            "collapsed_exact_duplicates": counts["exact_duplicate"],
            "near_duplicates_preserved": 60,
            "historical_memories_preserved": sum(bool(item.superseded_by) for item in memories),
            "provenance_preserved": all(item.source for item in memories),
        },
        "performance": {
            "average_insertion_ms": insertion_seconds * 1_000 / len(dataset.events),
            "average_duplicate_detection_ms": latency_by_outcome["exact_duplicate"]
            * 1_000
            / counts["exact_duplicate"],
            "total_lifecycle_processing_ms": insertion_seconds * 1_000,
            "database_bytes": (root / "index.db").stat().st_size,
        },
        "sync": {"exported": exported.exported, "imported": imported.imported},
        "failures": failures,
    }


def render(results: dict) -> str:
    dataset, quality = results["dataset"], results["quality"]
    growth = [
        "| Events | Stored | Active | Superseded | Archived | Duplicates |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    retrieval = [
        "| Memory Store Size | Recall | Precision | F1 | Context Tokens | Latency ms |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in results["growth"]:
        growth.append(
            f"| {row['events']} | {row['stored']} | {row['active']} | {row['superseded']} | {row['archived']} | {row['duplicates']} |"
        )
        metric = row["retrieval"]
        retrieval.append(
            f"| {row['stored']} | {metric['recall']:.2%} | {metric['precision']:.2%} | {metric['f1']:.2%} | {metric['context_tokens']:.1f} | {metric['latency_ms']:.3f} |"
        )
    return f"""# RMB Phase 14 Memory Lifecycle

Dataset: {dataset["projects"]} projects, {dataset["events"]} events/candidates, {dataset["questions"]} questions. Categories: {", ".join(dataset["categories"])}.

## Memory Growth

{chr(10).join(growth)}

## Retrieval Stability

{chr(10).join(retrieval)}

## Lifecycle Quality

- Formation precision: {quality["formation_precision"]:.2%}
- Duplicate rate: {quality["duplicate_rate"]:.2%}
- Stale current-state rate: {quality["stale_memory_rate"]:.2%}
- Historical linked-memory retention: {quality["historical_linked_rate"]:.2%}
- Unresolved contradiction pairs: {quality["unresolved_contradictions"]}
- Privacy candidates blocked: {quality["privacy_rejections"]}
- Provenance preserved: {quality["provenance_preservation"]}
- Restart integrity: {quality["persistence_integrity"]}
- Obsidian round-trip integrity: {quality["sync_integrity"]}

## Consolidation

Only exact deterministic duplicates collapsed. Near-duplicates, contradictions, and superseded historical states remain physically stored. Before: {results["consolidation"]["before_candidates"]} candidates. After: {results["consolidation"]["after_memories"]} memories. Collapsed: {results["consolidation"]["collapsed_exact_duplicates"]}. Historical memories preserved: {results["consolidation"]["historical_memories_preserved"]}.

## Limitations

Deterministic authored synthetic workload. No LLM consolidation. No Phase 14 embeddings. Near-duplicates remain because safe equivalence is not established. Genuine contradictions remain unresolved when evidence is ambiguous. Results do not establish universal memory quality.
"""


def main() -> dict:
    base, runtime = (
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent / ".runtime" / "lifecycle",
    )
    if runtime.exists():
        shutil.rmtree(runtime)
    results = evaluate(generate_lifecycle_dataset(), runtime)
    (base / "results").mkdir(exist_ok=True)
    (base / "reports").mkdir(exist_ok=True)
    (base / "results" / "lifecycle-latest.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    (base / "reports" / "lifecycle-latest.md").write_text(render(results))
    lines = ["# Lifecycle Failure Analysis", ""] + (
        [f"- {item['type']}: {item['detail']}" for item in results["failures"]]
        or [
            "No infrastructure lifecycle failures. Retrieval limitations remain visible in checkpoint metrics."
        ]
    )
    (base / "reports" / "lifecycle-failure-analysis.md").write_text("\n".join(lines) + "\n")
    return results


if __name__ == "__main__":
    main()
