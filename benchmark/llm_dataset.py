"""Synthetic, shareable Phase 12 long-context memory workload."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .dataset import Conversation, Dataset, Question

SPECS = (
    ("atlas", "PostgreSQL", "SQLite", "offline operation", "React", "Mira", "2026-10-15"),
    ("beacon", "MySQL", "DuckDB", "single-node analytics", "Vue", "Noah", "2026-10-22"),
    ("cedar", "MongoDB", "PostgreSQL", "transaction safety", "Angular", "Iris", "2026-11-01"),
    ("delta", "SQLite", "MySQL", "write concurrency", "Svelte", "Omar", "2026-11-08"),
    ("ember", "DuckDB", "MongoDB", "schema flexibility", "React", "Lina", "2026-11-15"),
    ("forge", "PostgreSQL", "DuckDB", "local analytics", "Vue", "Theo", "2026-11-22"),
    ("grove", "MySQL", "SQLite", "edge deployment", "Angular", "Asha", "2026-12-01"),
    ("harbor", "MongoDB", "PostgreSQL", "auditability", "Svelte", "Evan", "2026-12-08"),
    ("ion", "SQLite", "MongoDB", "rapid schema change", "React", "Zara", "2026-12-15"),
    ("juniper", "DuckDB", "MySQL", "replication support", "Vue", "Kai", "2026-12-22"),
)


def generate_llm_dataset() -> Dataset:
    """Create 10 projects, 400 sessions, 400 authored facts, and 120 questions."""
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)
    conversations: list[Conversation] = []
    questions: list[Question] = []
    for project_index, (project, old, current, reason, framework, owner, deadline) in enumerate(
        SPECS
    ):
        title, base = project.title(), project_index * 40
        records: dict[int, str] = {}

        def add(
            session: int,
            content: str,
            kind: str = "semantic",
            *,
            supersedes: str | None = None,
            project_name: str = project,
            record_map: dict[int, str] = records,
            project_base: int = base,
            project_owner: str = owner,
        ) -> str:
            source = f"{project_name}-llm-{session:02d}"
            record_map[session] = source
            conversations.append(
                Conversation(
                    source,
                    project_base + session,
                    project_name,
                    content,
                    kind,
                    start + timedelta(days=project_base + session),
                    (project_name, project_owner),
                    supersedes,
                )
            )
            return source

        original = add(
            1, f"January decision: {title} originally used {old} as primary database.", "decision"
        )
        rationale = add(
            2,
            f"January rationale: {title} rejected hosted storage because {reason} was required.",
            "constraint",
        )
        architecture = add(
            3,
            f"June architecture decision: {title} adopted {framework} for frontend implementation.",
            "decision",
        )
        preference = add(
            4, f"Team preference for {title}: concise weekly updates from {owner}.", "preference"
        )
        provenance = add(
            5,
            f"Requirement origin: {title} offline requirement came from {owner}'s design review.",
            "relationship",
        )
        migration = add(
            6,
            f"September decision: {title} migrated from {old} to {current} because {reason}.",
            "decision",
            supersedes=original,
        )
        add(
            7,
            f"Current state: {title} now uses {current} as primary database.",
            "decision",
            supersedes=migration,
        )
        add(8, f"Delivery constraint: {title} deadline is {deadline}.", "constraint")
        for session in range(9, 41):
            topic = (session * 7 + project_index) % 13
            add(
                session,
                f"Session {session} working note: {title} reviewed component-{topic}, "
                f"tutorial references PostgreSQL MySQL MongoDB SQLite DuckDB, no architecture decision changed.",
                "noise",
            )

        def question(
            suffix: str,
            category: str,
            text: str,
            sources: tuple[str, ...],
            facts: tuple[str, ...],
            *,
            provenance_required: bool = False,
            project_name: str = project,
        ) -> None:
            questions.append(
                Question(
                    f"{project_name}-{suffix}",
                    category,
                    text,
                    sources,
                    project_name,
                    None,
                    "phase12",
                    " | ".join(facts),
                    facts,
                    facts,
                    provenance_required,
                )
            )

        question(
            "current",
            "current_state",
            f"What database does {title} currently use?",
            (records[7],),
            (current,),
        )
        question(
            "historical",
            "historical",
            f"What database did {title} use before migration?",
            (original,),
            (old,),
        )
        question(
            "decision",
            "decision",
            f"Why was {current} selected for {title}?",
            (migration, rationale),
            (current, reason),
        )
        question(
            "preference",
            "preference",
            f"What update style does {title} prefer?",
            (preference,),
            ("concise weekly updates",),
        )
        question(
            "constraint",
            "constraint",
            f"What limitation prevented hosted storage for {title}?",
            (rationale,),
            (reason,),
        )
        question(
            "multi",
            "multi_memory",
            f"What database does {title} use now, what did it use before, and why did it change?",
            (original, migration, records[7]),
            (current, old, reason),
        )
        question(
            "temporal",
            "temporal",
            f"What was {title}'s architecture decision in June?",
            (architecture,),
            (framework,),
        )
        question(
            "provenance",
            "provenance",
            f"Where did {title}'s offline requirement originate?",
            (provenance,),
            (owner, "design review"),
            provenance_required=True,
        )
        question(
            "unsupported",
            "unsupported",
            f"What GPU did {title} use?",
            (),
            ("INSUFFICIENT EVIDENCE",),
        )
        question(
            "distractor",
            "distractor",
            f"Despite tutorial discussion, what primary database does {title} now use?",
            (records[7],),
            (current,),
        )
        question(
            "deadline",
            "current_state",
            f"What is {title}'s delivery deadline?",
            (records[8],),
            (deadline,),
        )
        question(
            "owner",
            "provenance",
            f"Who supplied {title}'s offline requirement?",
            (provenance,),
            (owner,),
        )
    return Dataset(
        tuple(conversations),
        tuple(questions),
        tuple(item[0] for item in SPECS),
        tuple(item[5] for item in SPECS),
    )
