"""Deterministic long-horizon lifecycle workload."""

from __future__ import annotations

from dataclasses import dataclass

from redstone.core.memory import MemoryType


@dataclass(frozen=True)
class LifecycleEvent:
    index: int
    source: str
    project: str
    content: str
    memory_type: MemoryType
    useful: bool
    supersedes_source: str | None = None
    archive: bool = False


@dataclass(frozen=True)
class LifecycleQuestion:
    id: str
    project: str
    query: str
    expected_sources: tuple[str, ...]
    category: str


@dataclass(frozen=True)
class LifecycleDataset:
    projects: tuple[str, ...]
    events: tuple[LifecycleEvent, ...]
    questions: tuple[LifecycleQuestion, ...]


def generate_lifecycle_dataset() -> LifecycleDataset:
    """Create 20 projects, 1,100 candidates, and 500 fixed questions."""
    projects = tuple(f"project-{index:02d}" for index in range(1, 21))
    events: list[LifecycleEvent] = []
    questions: list[LifecycleQuestion] = []
    states = ("PostgreSQL", "SQLite", "MySQL", "PostgreSQL")
    kinds = tuple(MemoryType)
    for project_number, project in enumerate(projects, 1):
        base = (project_number - 1) * 55

        def source(position: int, project_name: str = project) -> str:
            return f"{project_name}-event-{position:02d}"

        for position in range(1, 10):
            kind = kinds[position - 1]
            events.append(
                LifecycleEvent(
                    base + position,
                    source(position),
                    project,
                    f"{project} {kind.value} fact {position}: retained lifecycle evidence from session {position}.",
                    kind,
                    True,
                )
            )
        previous = None
        state_sources = []
        for offset, state in enumerate(states, 10):
            current_source = source(offset)
            wording = (
                "originally used" if offset == 10 else "migrated to" if offset < 13 else "now uses"
            )
            events.append(
                LifecycleEvent(
                    base + offset,
                    current_source,
                    project,
                    f"{project} {wording} {state} as primary database.",
                    MemoryType.DECISION,
                    True,
                    previous,
                )
            )
            state_sources.append(current_source)
            previous = current_source
        canonical = f"{project} backup retention is 30 days."
        for position in range(14, 19):
            events.append(
                LifecycleEvent(
                    base + position, source(position), project, canonical, MemoryType.SEMANTIC, True
                )
            )
        near = (
            f"The {project} backup period is 30 days.",
            f"30-day backups are retained by {project}.",
            f"{project} retains backups for 30 days.",
        )
        for position, content in enumerate(near, 19):
            events.append(
                LifecycleEvent(
                    base + position, source(position), project, content, MemoryType.SEMANTIC, True
                )
            )
        events.extend(
            (
                LifecycleEvent(
                    base + 22,
                    source(22),
                    project,
                    f"{project} deployment target is AWS; decision remains unresolved.",
                    MemoryType.DECISION,
                    True,
                ),
                LifecycleEvent(
                    base + 23,
                    source(23),
                    project,
                    f"{project} deployment target is GCP; decision remains unresolved.",
                    MemoryType.DECISION,
                    True,
                ),
            )
        )
        noise = ("Okay.", "That sounds good.", "Let's see.", "Interesting.")
        for position in range(24, 51):
            events.append(
                LifecycleEvent(
                    base + position,
                    source(position),
                    project,
                    noise[position % len(noise)],
                    MemoryType.EPISODIC,
                    False,
                )
            )
        secrets = (
            "password=unacceptablylongsecret",
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
            "sk_abcdefghijklmnopqrstuvwx",
        )
        for position, content in enumerate(secrets, 51):
            events.append(
                LifecycleEvent(
                    base + position, source(position), project, content, MemoryType.SEMANTIC, False
                )
            )
        events.append(
            LifecycleEvent(
                base + 54,
                source(54),
                project,
                f"{project} obsolete setup procedure retained for audit.",
                MemoryType.PROCEDURAL,
                True,
                archive=True,
            )
        )
        events.append(
            LifecycleEvent(
                base + 55,
                source(55),
                project,
                f"{project} current owner is owner-{project_number:02d}.",
                MemoryType.RELATIONSHIP,
                True,
            )
        )
        templates = (
            ("current", f"What database does {project} use now?", (state_sources[-1],)),
            ("historical", f"What database did {project} originally use?", (state_sources[0],)),
            ("timeline", f"Show {project} database timeline.", tuple(state_sources)),
            ("duplicate", f"What is {project} backup retention?", (source(14),)),
            (
                "conflict",
                f"Which deployment targets conflict for {project}?",
                (source(22), source(23)),
            ),
        )
        for repeat in range(5):
            for category, query, expected in templates:
                questions.append(
                    LifecycleQuestion(
                        f"{project}-{category}-{repeat}", project, query, expected, category
                    )
                )
    return LifecycleDataset(projects, tuple(events), tuple(questions))
