"""Deterministic hard long-term memory dataset for RMB."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class Conversation:
    id: str
    index: int
    project: str | None
    content: str
    kind: str
    observed_at: datetime
    entities: tuple[str, ...] = ()
    supersedes_source: str | None = None
    related_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    question: str
    expected_sources: tuple[str, ...]
    expected_project: str | None
    expected_time: int | None
    difficulty: str
    expected_answer: str = ""
    acceptable_answers: tuple[str, ...] = ()
    required_facts: tuple[str, ...] = ()
    requires_provenance: bool = False


@dataclass(frozen=True)
class Dataset:
    conversations: tuple[Conversation, ...]
    questions: tuple[Question, ...]
    projects: tuple[str, ...]
    entities: tuple[str, ...]


PROJECTS = ("atlas", "nova", "orion", "redstone", "helix")
ENTITIES = tuple(f"person-{index:02d}" for index in range(1, 26))
DATABASES = ("PostgreSQL", "MySQL", "MongoDB", "SQLite", "DuckDB")
FRAMEWORKS = ("React", "Vue", "Angular", "Svelte", "SolidJS")


def generate_dataset(seed: int = 8128, conversation_count: int = 220) -> Dataset:
    """Generate project cross-talk, state changes, and heavy noise."""
    randomizer = random.Random(seed)
    start = datetime(2025, 1, 1, 9, tzinfo=UTC)
    records: dict[int, Conversation] = {}

    def add(index: int, project: str | None, content: str, kind: str, entities: tuple[str, ...] = (), supersedes: str | None = None, related: tuple[str, ...] = ()) -> str:
        source = f"conversation-{index:03d}"
        records[index] = Conversation(source, index, project, content, kind, start + timedelta(days=index), entities, supersedes, related)
        return source

    originals: dict[str, str] = {}
    currents: dict[str, str] = {}
    frameworks: dict[str, tuple[str, str]] = {}
    for offset, project in enumerate(PROJECTS):
        original_index = 3 + offset * 4
        current_index = 130 + offset * 8
        owner = ENTITIES[offset]
        originals[project] = add(original_index, project, f"{project.title()} originally chose {DATABASES[offset]} as primary database. Decision owner was {owner}.", "decision", (project, owner))
        currents[project] = add(current_index, project, f"{project.title()} now uses {DATABASES[(offset + 2) % len(DATABASES)]} as primary database.", "decision", (project,), originals[project])
        old = add(24 + offset * 3, project, f"{project.title()} originally selected {FRAMEWORKS[offset]} for dashboard framework.", "decision", (project,))
        new = add(168 + offset * 4, project, f"{project.title()} currently uses {FRAMEWORKS[(offset + 2) % len(FRAMEWORKS)]} for dashboard framework.", "decision", (project,), old)
        frameworks[project] = (old, new)

    preference_sources: list[tuple[str, str]] = []
    preferences = (("report style", "verbose narratives", "concise bullet summaries"), ("primary language", "Java", "Python"), ("meeting time", "afternoons", "mornings"), ("test output", "full traces", "failure summaries"), ("editor theme", "light", "dark"), ("package manager", "pip", "uv"), ("line length", "88 columns", "100 columns"), ("documentation", "tutorials", "reference pages"), ("release cadence", "monthly", "weekly"), ("terminal shell", "cmd", "PowerShell"))
    preference_current_indexes = (151, 153, 155, 157, 159, 187, 191, 195, 199, 203)
    for offset, (topic, old, new) in enumerate(preferences):
        old_source = add(42 + offset * 6, "preferences", f"User originally preferred {old} for {topic}.", "preference", ("user",))
        new_source = add(preference_current_indexes[offset], "preferences", f"User now prefers {new} for {topic}.", "preference", ("user",), old_source)
        preference_sources.append((old_source, new_source))

    for index in range(30, 125, 5):
        if index not in records:
            project = PROJECTS[(index // 5) % len(PROJECTS)]
            owner = ENTITIES[index % len(ENTITIES)]
            add(index, project, f"{project.title()} decision {index}: use component-{index % 11} for pipeline stage-{index % 7}; owner {owner}.", "decision", (project, owner))

    noise = (
        "Team discussed football results and weekend travel plans.",
        "A Docker image cleanup was mentioned without any project decision.",
        "Python and Java training materials were compared casually.",
        "React, Vue, and Svelte release notes were reviewed without changing architecture.",
        "PostgreSQL, SQLite, MongoDB, and MySQL appeared in an unrelated tutorial.",
        "Lunch preferences and office furniture were discussed.",
    )
    for index in range(1, conversation_count + 1):
        if index not in records:
            project = PROJECTS[index % len(PROJECTS)] if index % 3 else None
            add(index, project, f"{noise[index % len(noise)]} Reference {randomizer.randint(1000, 9999)}.", "noise")

    owner_sources: dict[str, str] = {}
    constraint_sources: dict[str, str] = {}
    for offset, project in enumerate(PROJECTS):
        owner_sources[project] = add(120 + offset * 2, project, f"{ENTITIES[offset]} owns {project.title()} database migration approval.", "relationship", (project, ENTITIES[offset]))
        constraint_sources[project] = add(121 + offset * 2, project, f"{project.title()} database must work offline; this reliability constraint drives storage selection.", "constraint", (project,))
        current_index = int(currents[project][-3:])
        records[current_index] = Conversation(**{**records[current_index].__dict__, "related_sources": (owner_sources[project], constraint_sources[project])})
    contradiction_a = add(206, "helix", "Helix deployment region is Europe-West.", "semantic", ("helix",))
    contradiction_b = add(207, "helix", "Helix deployment region is Asia-South.", "semantic", ("helix",))
    canonical_repeat = add(211, "redstone", "Redstone backup retention is 30 days.", "semantic", ("redstone",))
    for index in (212, 213, 214):
        add(index, "redstone", "Redstone backup retention is 30 days.", "semantic", ("redstone",))
    recent_source = add(219, "nova", "Nova release captain this week is person-21.", "episodic", ("nova", "person-21"))

    questions: list[Question] = []
    for project in PROJECTS:
        questions.extend((
            Question(f"{project}-database-current", "current_state", f"What storage engine backs {project.title()} now?", (currents[project],), project, None, "hard"),
            Question(f"{project}-database-original", "historical_state", f"What persistence technology did {project.title()} begin with?", (originals[project],), project, None, "hard"),
            Question(f"{project}-database-change", "temporal", f"When did {project.title()} change its primary database?", (originals[project], currents[project]), project, int(currents[project][-3:]), "hard"),
            Question(f"{project}-framework-current", "supersession", f"Which UI stack powers {project.title()} today?", (frameworks[project][1],), project, None, "hard"),
            Question(f"{project}-framework-original", "decision", f"What dashboard framework did {project.title()} originally select?", (frameworks[project][0],), project, None, "hard"),
            Question(f"{project}-provenance", "provenance", f"Which conversation supports {project.title()}'s current database decision?", (currents[project],), project, None, "hard"),
            Question(f"{project}-database-comparison", "comparison", f"Compare {project.title()}'s original and current primary database.", (originals[project], currents[project]), project, None, "hard"),
            Question(f"{project}-framework-comparison", "comparison", f"Compare {project.title()}'s original and current dashboard framework.", frameworks[project], project, None, "hard"),
            Question(f"{project}-decision-composition", "multi_memory", f"What database decision changed from original to current for {project.title()}, why, and cite its source?", (originals[project], currents[project], constraint_sources[project]), project, None, "hard"),
        ))
    for index, (old_source, new_source) in enumerate(preference_sources):
        topic = preferences[index][0]
        questions.extend((
            Question(f"preference-{index}-current", "preference", f"What does user currently prefer for {topic}?", (new_source,), "preferences", None, "hard"),
            Question(f"preference-{index}-original", "historical_state", f"What did user originally prefer for {topic}?", (old_source,), "preferences", None, "hard"),
        ))
    questions.extend((
        Question("atlas-multi-hop", "multi_hop", "Which database does Atlas use now, who approved it, and what constraint caused it?", (currents["atlas"], owner_sources["atlas"], constraint_sources["atlas"]), "atlas", None, "hard"),
        Question("redstone-distractor", "distractor", "What is Redstone's current primary database despite unrelated database tutorials?", (currents["redstone"],), "redstone", None, "hard"),
        Question("atlas-long-range", "long_term", "What primary database did Atlas originally choose?", (originals["atlas"],), "atlas", None, "hard"),
        Question("nova-project", "project", "What primary database does Nova use now?", (currents["nova"],), "nova", None, "hard"),
        Question("helix-contradiction", "contradiction", "Which conflicting deployment regions were recorded for Helix?", (contradiction_a, contradiction_b), "helix", None, "hard"),
        Question("redstone-redundancy", "redundancy", "What is Redstone backup retention?", (canonical_repeat,), "redstone", None, "medium"),
        Question("nova-short-term", "short_term", "Who is Nova release captain this week?", (recent_source,), "nova", None, "easy"),
    ))
    questions = [
        replace(
            question,
            expected_answer=" | ".join(records[int(source[-3:])].content for source in question.expected_sources),
        )
        for question in questions
    ]
    return Dataset(tuple(records[index] for index in sorted(records)), tuple(questions), PROJECTS, ENTITIES)
