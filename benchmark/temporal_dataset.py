"""Authored deterministic temporal/conflict composition workload."""

from __future__ import annotations

from datetime import UTC, datetime

from .dataset import Conversation, Dataset, Question


def generate_temporal_dataset() -> Dataset:
    projects = tuple(f"temporal-{index:02d}" for index in range(1, 21))
    conversations: list[Conversation] = []
    questions: list[Question] = []
    states = (
        "PostgreSQL",
        "SQLite",
        "MySQL",
        "DuckDB",
        "MongoDB",
        "MariaDB",
        "CockroachDB",
        "Firebird",
        "Oracle",
        "PostgreSQL",
    )
    for project_number, project in enumerate(projects, 1):
        state_sources = []
        previous = None
        for month, state in enumerate(states, 1):
            source = f"{project}-state-{month:02d}"
            conversations.append(
                Conversation(
                    source,
                    project_number * 100 + month,
                    project,
                    f"{project} database state is {state}; revision {month}.",
                    "decision",
                    datetime(2026, month, 1, tzinfo=UTC),
                    (project,),
                    previous,
                )
            )
            state_sources.append(source)
            previous = source
        aws, gcp = f"{project}-conflict-aws", f"{project}-conflict-gcp"
        conversations.extend(
            (
                Conversation(
                    aws,
                    project_number * 100 + 20,
                    project,
                    f"{project} deployment target is AWS; claim is unresolved.",
                    "decision",
                    datetime(2026, 11, 1, tzinfo=UTC),
                    (project, "deployment"),
                ),
                Conversation(
                    gcp,
                    project_number * 100 + 21,
                    project,
                    f"{project} deployment target is GCP; claim is unresolved.",
                    "decision",
                    datetime(2026, 11, 1, tzinfo=UTC),
                    (project, "deployment"),
                ),
                Conversation(
                    f"{project}-web",
                    project_number * 100 + 22,
                    project,
                    f"{project} Web database is PostgreSQL.",
                    "semantic",
                    datetime(2026, 12, 1, tzinfo=UTC),
                    (project, "web"),
                ),
                Conversation(
                    f"{project}-mobile",
                    project_number * 100 + 23,
                    project,
                    f"{project} Mobile database is SQLite.",
                    "semantic",
                    datetime(2026, 12, 1, tzinfo=UTC),
                    (project, "mobile"),
                ),
            )
        )
        templates = (
            ("current", f"What is {project}'s current database state?", (state_sources[-1],)),
            ("historical", f"What was {project}'s original database state?", (state_sources[0],)),
            ("timeline", f"Show {project}'s database timeline over time.", tuple(state_sources)),
            ("date", f"What database state was active in June for {project}?", (state_sources[5],)),
            (
                "resolved",
                f"Which database revisions in {project}'s timeline were resolved by supersession?",
                (state_sources[-2], state_sources[-1]),
            ),
            ("unresolved", f"Which deployment claims conflict for {project}?", (aws, gcp)),
            (
                "context",
                f"Do {project} Web and Mobile database choices conflict?",
                (f"{project}-web", f"{project}-mobile"),
            ),
            (
                "decision",
                f"What decisions were made for {project}'s database?",
                tuple(state_sources),
            ),
            (
                "partial",
                f"What was {project}'s database state in May before June?",
                (state_sources[4],),
            ),
            ("provenance", f"Which sources support {project}'s timeline?", tuple(state_sources)),
            (
                "mixed",
                f"Show {project}'s timeline and unresolved deployment conflicts.",
                tuple(state_sources) + (aws, gcp),
            ),
            (
                "three_state",
                f"Give first three states in {project}'s timeline.",
                tuple(state_sources[:3]),
            ),
            (
                "five_state",
                f"Give first five states in {project}'s timeline.",
                tuple(state_sources[:5]),
            ),
        )
        project_questions = []
        for repeat in range(2):
            for category, query, sources in templates:
                project_questions.append(
                    Question(
                        f"{project}-{category}-{repeat}",
                        category,
                        query,
                        sources,
                        project,
                        None,
                        "phase15",
                    )
                )
        questions.extend(project_questions[:25])
    return Dataset(tuple(conversations), tuple(questions), projects, ())
