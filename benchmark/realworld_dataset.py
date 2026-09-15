"""Authored public-style long-running project histories for answer-level RMB."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .dataset import Conversation, Dataset, Question

SPECS = (
    ("atlas", "PostgreSQL", "SQLite", "offline operation", "event-sourced", "Mira", "2026-10-15", "concise updates"),
    ("beacon", "MySQL", "DuckDB", "single-node analytics", "columnar", "Noah", "2026-10-22", "weekly demos"),
    ("cedar", "MongoDB", "PostgreSQL", "transaction safety", "hexagonal", "Iris", "2026-11-01", "typed APIs"),
    ("delta", "SQLite", "MySQL", "write concurrency", "service-oriented", "Omar", "2026-11-08", "short reports"),
    ("ember", "DuckDB", "MongoDB", "schema flexibility", "document-driven", "Lina", "2026-11-15", "dark themes"),
    ("forge", "PostgreSQL", "DuckDB", "local analytics", "pipeline-first", "Theo", "2026-11-22", "Python tooling"),
    ("grove", "MySQL", "SQLite", "edge deployment", "offline-first", "Asha", "2026-12-01", "small releases"),
    ("harbor", "MongoDB", "PostgreSQL", "auditability", "layered", "Evan", "2026-12-08", "reference docs"),
    ("ion", "SQLite", "MongoDB", "rapid schema change", "modular", "Zara", "2026-12-15", "visual reviews"),
    ("juniper", "DuckDB", "MySQL", "replication support", "message-driven", "Kai", "2026-12-22", "morning meetings"),
)


def generate_realworld_dataset() -> Dataset:
    """Create ten projects with ten ordered sessions and grounded questions."""
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)
    conversations: list[Conversation] = []
    questions: list[Question] = []
    entities: set[str] = set()
    for project_index, spec in enumerate(SPECS):
        project, old, new, constraint, architecture, owner, deadline, preference = spec
        title = project.title()
        entities.add(owner.casefold())
        base = project_index * 10

        def add(
            session: int,
            content: str,
            kind: str,
            *,
            supersedes: str | None = None,
            related: tuple[str, ...] = (),
            people: tuple[str, ...] = (),
            project_name: str = project,
            project_base: int = base,
        ) -> str:
            source = f"{project_name}-session-{session:02d}"
            conversations.append(
                Conversation(
                    source,
                    project_base + session,
                    project_name,
                    content,
                    kind,
                    start + timedelta(days=project_base + session),
                    (project_name, *people),
                    supersedes,
                    related,
                )
            )
            return source

        add(1, f"{title} began as a planning workspace for a public-style product case study.", "project")
        original = add(2, f"{title} originally used {old} as its primary database.", "decision")
        constraint_source = add(
            3,
            f"{title} must support {constraint}; {constraint} is the binding architecture constraint.",
            "constraint",
        )
        add(4, f"{title} initially used a monolithic architecture while scope remained small.", "decision")
        add(5, f"Testing found the old database design could not satisfy {constraint} reliably.", "episodic")
        switch = add(
            6,
            f"{title} switched from {old} to {new} because {constraint} was required.",
            "decision",
            supersedes=original,
            related=(constraint_source,),
        )
        owner_source = add(
            7,
            f"{owner} approved {title}'s database change to {new}.",
            "relationship",
            related=(switch,),
            people=(owner,),
        )
        add(
            8,
            f"Team reviewed unrelated {old}, {new}, and Redis tutorials; no architecture decision changed.",
            "episodic",
        )
        preference_source = add(
            9,
            f"For {title}, user now prefers {preference} for collaboration.",
            "preference",
        )
        final = add(
            10,
            f"{title} currently uses {new} with {architecture} architecture. Delivery deadline is {deadline}.",
            "decision",
            supersedes=switch,
            related=(constraint_source, owner_source, preference_source),
        )

        def question(
            suffix: str,
            category: str,
            text: str,
            sources: tuple[str, ...],
            facts: tuple[str, ...],
            *,
            project_scope: str | None = project,
            provenance: bool = False,
            project_name: str = project,
        ) -> None:
            questions.append(
                Question(
                    f"{project_name}-{suffix}",
                    category,
                    text,
                    sources,
                    project_scope,
                    None,
                    "realistic",
                    " ".join(facts),
                    (" ".join(facts),),
                    facts,
                    provenance,
                )
            )

        question("current", "current_state", f"What database does {title} currently use?", (final,), (new,))
        question("historical", "historical_state", f"What database did {title} originally use?", (original,), (old,))
        question("decision", "decision", f"What database did {title} choose and why?", (switch,), (new, constraint))
        question("timeline", "timeline", f"What did {title} use originally and what does it use currently?", (original, final), (old, new))
        question("project", "project", f"Which project uses {architecture} architecture?", (final,), (title, architecture), project_scope=None)
        question("preference", "preference", f"What does user currently prefer for {title}?", (preference_source,), (preference,))
        question("comparison", "comparison", f"Compare {title}'s original database with the database currently used.", (original, final), (old, new))
        question("multi", "multi_memory", f"What are {title}'s current database and architecture, and why?", (final, constraint_source), (new, architecture, constraint))
        question("provenance", "provenance", f"Which session is the source for {title}'s current primary database decision?", (final,), (final,), provenance=True)
        question("constraint", "constraint", f"What constraint caused {title}'s database change?", (switch,), (constraint,))
        question("distractor", "distractor", f"Despite tutorial chatter, what database does {title} currently use?", (final,), (new,))
    return Dataset(
        tuple(conversations),
        tuple(questions),
        tuple(spec[0] for spec in SPECS),
        tuple(sorted(entities)),
    )
