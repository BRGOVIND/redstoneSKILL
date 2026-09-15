from pathlib import Path

import pytest

from benchmark.answers import ProviderConfigurationError, provider_from_environment
from benchmark.llm_dataset import generate_llm_dataset
from benchmark.llm_evaluation import HISTORY_LENGTHS, evaluate_llm


def test_phase12_dataset_is_synthetic_and_large_enough() -> None:
    dataset = generate_llm_dataset()
    assert len(dataset.projects) == 10
    assert len(dataset.conversations) == 400
    assert len(dataset.questions) == 120
    assert {
        "current_state",
        "historical",
        "decision",
        "preference",
        "constraint",
        "multi_memory",
        "temporal",
        "provenance",
        "unsupported",
        "distractor",
    } <= {item.category for item in dataset.questions}
    assert HISTORY_LENGTHS == (1_000, 5_000, 10_000, 25_000, 50_000)


def test_openai_provider_requires_environment_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("REDSTONE_LLM_MODEL", raising=False)
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        provider_from_environment("openai")


def test_phase12_evaluation_separates_equal_and_full_history(tmp_path: Path) -> None:
    dataset = generate_llm_dataset()
    provider = provider_from_environment("deterministic")
    equal = evaluate_llm(dataset, tmp_path / "equal", provider, max_questions=3)
    full = evaluate_llm(dataset, tmp_path / "full", provider, full_history=True, max_questions=3)
    assert equal["configuration"]["comparison"] == "equal_budget"
    assert full["configuration"]["comparison"] == "full_history"
    assert equal["dataset"]["important_facts"] >= 300
    assert all("baseline" in row["blind_candidate_labels"] for row in equal["questions"])
