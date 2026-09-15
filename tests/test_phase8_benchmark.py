from pathlib import Path

from benchmark.dataset import generate_dataset
from benchmark.evaluation import evaluate
from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.retrieval.context import build_context
from redstone.retrieval.query import QueryIntent, parse_intent, query_terms
from redstone.storage.sqlite import SQLiteMemoryStore


def test_hard_dataset_is_deterministic_and_meets_scale() -> None:
    first = generate_dataset()
    second = generate_dataset()
    assert first == second
    assert len(first.conversations) >= 200
    assert len(first.projects) >= 5
    assert len(first.entities) >= 20
    assert sum(len(question.expected_sources) > 1 for question in first.questions) >= 20
    assert sum(item.kind == "decision" for item in first.conversations) >= 30
    assert sum(item.kind == "preference" for item in first.conversations) >= 20
    assert all(question.expected_answer for question in first.questions)
    assert {
        "short_term",
        "long_term",
        "project",
        "decision",
        "preference",
        "temporal",
        "supersession",
        "contradiction",
        "multi_hop",
        "provenance",
        "distractor",
        "redundancy",
    } <= {question.category for question in first.questions}


def test_query_intent_and_temporal_retrieval(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    old, _ = manager.remember(
        "Atlas originally chose PostgreSQL database.", MemoryType.DECISION, project="atlas"
    )
    new, _ = manager.remember(
        "Atlas now uses SQLite database.", MemoryType.DECISION, project="atlas"
    )
    manager.supersede(old.id, new.id)
    assert parse_intent("What does Atlas use now?") == QueryIntent.CURRENT
    assert "database" in query_terms("What storage engine backs Atlas?")
    assert (
        manager.search("Which database does Atlas use now?", project="atlas")[0].memory.id == new.id
    )
    assert (
        manager.search("Which database did Atlas originally choose?", project="atlas")[0].memory.id
        == old.id
    )


def test_project_distractors_duplicates_context_and_provenance(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    expected, _ = manager.remember(
        "Atlas uses SQLite database.", project="atlas", source="conversation-001"
    )
    manager.remember("Nova uses PostgreSQL database.", project="nova")
    for index in range(40):
        manager.remember(f"Atlas unrelated football note {index}.", project="atlas", importance=0.1)
    duplicate, created = manager.remember("  Atlas uses SQLite database. ", project="atlas")
    assert created is False and duplicate.id == expected.id
    results = manager.search("Atlas SQLite database", project="atlas", limit=3)
    assert results[0].memory.id == expected.id
    context = build_context(
        results, project="atlas", max_chars=300, query="What is current database?"
    )
    assert len(context) <= 300
    assert "conversation-001" in context


def test_benchmark_metrics_are_reproducible_except_latency(tmp_path: Path) -> None:
    dataset = generate_dataset()
    first = evaluate(dataset, tmp_path / "first", top_k=3)
    second = evaluate(dataset, tmp_path / "second", top_k=3)
    first["redstone"].pop("latency_ms")
    second["redstone"].pop("latency_ms")
    first["adaptive"].pop("latency_ms")
    second["adaptive"].pop("latency_ms")
    assert first == second
    assert first["adaptive"]["recall"] > first["redstone"]["recall"]
