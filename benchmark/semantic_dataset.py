"""Targeted paraphrase subset derived from Phase 12 authored history."""

from __future__ import annotations

from dataclasses import replace

from .dataset import Dataset, Question
from .llm_dataset import generate_llm_dataset


def generate_semantic_dataset() -> Dataset:
    base = generate_llm_dataset()
    by_id = {question.id: question for question in base.questions}
    questions: list[Question] = []
    for project in base.projects:
        title = project.title()
        originals = (
            ("decision", f"Why was {title}'s current database selected?"),
            ("current", f"Which data store powers {title} nowadays?"),
            ("historical", f"Which engine preceded {title}'s switch?"),
            ("temporal", f"Which frontend direction did {title} settle on midyear?"),
            ("provenance", f"Who brought {title}'s offline rule to design review?"),
        )
        for suffix, wording in originals:
            source = by_id[f"{project}-{suffix}"]
            questions.append(
                replace(
                    source,
                    id=f"semantic-{source.id}",
                    question=wording,
                    category="semantic_paraphrase",
                )
            )
    return Dataset(base.conversations, tuple(questions), base.projects, base.entities)
