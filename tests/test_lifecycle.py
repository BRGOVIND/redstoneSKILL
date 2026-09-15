from pathlib import Path

from benchmark.lifecycle_dataset import generate_lifecycle_dataset
from redstone.core.formation import MemoryCandidate, reject_reason
from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.storage.sqlite import SQLiteMemoryStore


def test_lifecycle_dataset_scale_and_categories() -> None:
    dataset = generate_lifecycle_dataset()
    assert len(dataset.projects) == 20
    assert len(dataset.events) == 1_100
    assert len(dataset.questions) == 500
    assert set(MemoryType) == {event.memory_type for event in dataset.events}


def test_candidate_formation_rejects_noise_and_privacy(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    noise = MemoryCandidate("Okay.", MemoryType.EPISODIC, "session-1")
    secret = MemoryCandidate("password=unacceptablylongsecret", MemoryType.SEMANTIC, "session-2")
    assert reject_reason(noise) == "low_value_noise"
    assert (
        reject_reason(MemoryCandidate("That sounds good.", MemoryType.EPISODIC, "s"))
        == "low_value_noise"
    )
    assert manager.remember_candidate(noise)[2] == "low_value_noise"
    assert manager.remember_candidate(secret)[2] == "privacy_rejection"
    assert manager.stats()["total"] == 0


def test_duplicate_supersession_history_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "index.db"
    manager = MemoryManager(SQLiteMemoryStore(path))
    first, created, _ = manager.remember_candidate(
        MemoryCandidate(
            "Atlas originally used PostgreSQL.", MemoryType.DECISION, "session-1", "atlas"
        )
    )
    duplicate, duplicate_created, reason = manager.remember_candidate(
        MemoryCandidate(
            "Atlas originally used PostgreSQL.", MemoryType.DECISION, "session-2", "atlas"
        )
    )
    current, _, _ = manager.remember_candidate(
        MemoryCandidate("Atlas now uses SQLite.", MemoryType.DECISION, "session-3", "atlas")
    )
    assert first and current and duplicate
    assert created and not duplicate_created and reason == "exact_duplicate"
    manager.supersede(first.id, current.id)
    assert (
        manager.retrieve_adaptive("What did Atlas originally use?", project="atlas")
        .results[0]
        .memory.id
        == first.id
    )
    assert (
        manager.retrieve_adaptive("What does Atlas use now?", project="atlas").results[0].memory.id
        == current.id
    )
    restarted = MemoryManager(SQLiteMemoryStore(path))
    assert restarted.store.get(first.id).superseded_by == current.id
    assert restarted.store.get(first.id).source == "session-1"
