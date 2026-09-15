from pathlib import Path

from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.retrieval.context import build_adaptive_context
from redstone.retrieval.query import InformationRequirement, QueryIntent, analyze_query
from redstone.storage.sqlite import SQLiteMemoryStore


def manager_at(tmp_path: Path) -> MemoryManager:
    return MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))


def test_query_analysis_exposes_specific_intents() -> None:
    assert analyze_query("What decision did Atlas make?").intent == QueryIntent.DECISION
    assert analyze_query("What does the user prefer?").intent == QueryIntent.PREFERENCE
    assert analyze_query("Which project owns SQLite?").intent == QueryIntent.PROJECT
    assert analyze_query("What is related to Atlas?").intent == QueryIntent.RELATED


def test_single_fact_selects_one_primary_memory(tmp_path: Path) -> None:
    manager = manager_at(tmp_path)
    memory, _ = manager.remember(
        "Atlas uses SQLite database.", project="atlas", source="conversation-001"
    )
    selection = manager.retrieve_adaptive("What database does Atlas use?", project="atlas")
    assert [result.memory.id for result in selection.results] == [memory.id]
    assert selection.coverage == 1.0


def test_temporal_comparison_selects_current_and_history(tmp_path: Path) -> None:
    manager = manager_at(tmp_path)
    old, _ = manager.remember(
        "Atlas originally used PostgreSQL database.", MemoryType.DECISION, project="atlas"
    )
    current, _ = manager.remember(
        "Atlas now uses SQLite database.", MemoryType.DECISION, project="atlas"
    )
    manager.supersede(old.id, current.id)
    analysis = analyze_query("What database does Atlas use now and what did it use before?")
    selection = manager.retrieve_adaptive(
        "What database does Atlas use now and what did it use before?", project="atlas"
    )
    assert analysis.intent == QueryIntent.COMPARISON
    assert set(analysis.requirements) >= {
        InformationRequirement.CURRENT,
        InformationRequirement.HISTORICAL,
    }
    assert {result.memory.id for result in selection.results} == {old.id, current.id}


def test_multi_hop_expands_only_complementary_relationships(tmp_path: Path) -> None:
    manager = manager_at(tmp_path)
    decision, _ = manager.remember(
        "Atlas now uses SQLite database.", MemoryType.DECISION, project="atlas"
    )
    owner, _ = manager.remember(
        "Person-01 approved Atlas migration.",
        MemoryType.RELATIONSHIP,
        project="atlas",
        entities=["person-01"],
    )
    reason, _ = manager.remember(
        "Atlas requires offline reliability.", MemoryType.CONSTRAINT, project="atlas"
    )
    manager.link(decision.id, owner.id)
    manager.link(decision.id, reason.id)
    selection = manager.retrieve_adaptive(
        "What does Atlas use now, who approved it, and why?", project="atlas"
    )
    assert {result.memory.id for result in selection.results} == {decision.id, owner.id, reason.id}
    assert selection.coverage == 1.0


def test_redundancy_project_scope_budget_and_context_provenance(tmp_path: Path) -> None:
    manager = manager_at(tmp_path)
    primary, _ = manager.remember(
        "Atlas uses SQLite for storage.",
        project="atlas",
        source="conversation-010",
        importance=0.9,
    )
    manager.remember("Atlas storage uses SQLite database.", project="atlas")
    reason, _ = manager.remember(
        "Atlas chose storage because offline reliability is required.",
        MemoryType.CONSTRAINT,
        project="atlas",
    )
    manager.remember("Nova uses SQLite for storage.", project="nova")
    manager.link(primary.id, reason.id)
    selection = manager.retrieve_adaptive(
        "Which project uses SQLite storage and why?", project="atlas", max_tokens=40
    )
    assert all(result.memory.project == "atlas" for result in selection.results)
    assert len(selection.results) == 2
    assert selection.context_tokens <= 40
    context = build_adaptive_context(selection, project="atlas", max_tokens=120)
    assert primary.id in context
    assert "conversation-010" in context
    assert "Score:" in context and "Reason:" in context
