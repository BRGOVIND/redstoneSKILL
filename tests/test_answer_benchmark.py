from pathlib import Path

from benchmark.answer_evaluation import attribute_failure, evaluate_answers
from benchmark.answers import DeterministicAnswerProvider, normalize, score_answer
from benchmark.realworld_dataset import generate_realworld_dataset


def test_realworld_dataset_has_grounded_long_running_projects() -> None:
    dataset = generate_realworld_dataset()
    assert len(dataset.projects) >= 10
    assert len(dataset.conversations) >= len(dataset.projects) * 10
    assert len(dataset.questions) == 110
    assert all(
        question.required_facts and question.expected_sources for question in dataset.questions
    )
    assert {
        "current_state",
        "historical_state",
        "decision",
        "timeline",
        "project",
        "preference",
        "comparison",
        "multi_memory",
        "provenance",
        "constraint",
        "distractor",
    } <= {question.category for question in dataset.questions}


def test_answer_scoring_supports_normalized_facts_and_provenance() -> None:
    context = "[source=atlas-session-10] Atlas currently uses SQLite."
    answer = "ATLAS currently uses SQLite! Source: atlas-session-10"
    score = score_answer(
        answer,
        context,
        expected_answer="SQLite",
        acceptable_answers=("Atlas uses SQLite",),
        required_facts=("SQLite",),
        required_sources=("atlas-session-10",),
        requires_provenance=True,
    )
    assert normalize(" SQLite! ") == "sqlite"
    assert score.accuracy == 1.0
    assert score.fact_coverage == 1.0
    assert score.factuality == 1.0
    assert score.provenance_accuracy == 1.0


def test_failure_attribution_separates_pipeline_levels() -> None:
    assert attribute_failure(False, False, False) == "retrieval_failure"
    assert attribute_failure(True, False, False) == "context_failure"
    assert attribute_failure(True, True, False) == "answer_generation_failure"
    assert attribute_failure(True, True, True, False) == "evaluation_failure"
    assert attribute_failure(True, True, True) is None


def test_deterministic_provider_uses_only_supplied_context() -> None:
    provider = DeterministicAnswerProvider()
    context = "[source=a] Atlas currently uses SQLite.\n[source=b] Nova uses MySQL."
    answer = provider.answer("What does Atlas currently use?", context)
    assert "SQLite" in answer
    assert "MySQL" not in answer


def test_answer_benchmark_separates_pipeline_levels(tmp_path: Path) -> None:
    results = evaluate_answers(generate_realworld_dataset(), tmp_path / "answer")
    assert results["redstone"]["answer_accuracy"] > results["baseline"]["answer_accuracy"]
    assert results["redstone"]["context_pass_rate"] == 1.0
    assert results["redstone"]["answer_factuality"] == 1.0
    assert any(
        not row["redstone_retrieval_pass"]
        and row["redstone_context_pass"]
        and row["redstone_answer_score"]["accuracy"]
        for row in results["questions"]
    )
