from pathlib import Path

from redstone.core.manager import MemoryManager
from redstone.obsidian.adapter import ObsidianAdapter
from redstone.obsidian.serializer import (
    markdown_to_memory,
    memory_to_markdown,
    normalized_hash,
    safe_filename,
)
from redstone.storage.sqlite import SQLiteMemoryStore


def build_adapter(tmp_path: Path) -> tuple[MemoryManager, ObsidianAdapter]:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    return manager, ObsidianAdapter(tmp_path / "Redstone Vault", manager.store)


def test_serializer_is_stable_parseable_and_safe(tmp_path: Path) -> None:
    manager, _ = build_adapter(tmp_path)
    memory, _ = manager.remember("Unicode memory: cafe and symbols < > /.", tags=["Red Stone"])
    rendered = memory_to_markdown(memory)
    assert rendered == memory_to_markdown(memory)
    assert 'redstone_id: "' in rendered
    assert markdown_to_memory(rendered).content == memory.content
    assert ".." not in safe_filename(memory)
    assert "/" not in safe_filename(memory)
    assert normalized_hash("same text  \r\n") == normalized_hash("same text\n")


def test_vault_initialization_is_non_destructive(tmp_path: Path) -> None:
    _, adapter = build_adapter(tmp_path)
    unrelated = adapter.vault / "keep.txt"
    adapter.vault.mkdir()
    unrelated.write_text("keep", encoding="utf-8")
    adapter.initialize_vault()
    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert (adapter.vault / "Memories" / "Semantic").is_dir()
    assert (adapter.vault / ".redstone" / "config.json").is_file()


def test_export_sync_and_archive(tmp_path: Path) -> None:
    manager, adapter = build_adapter(tmp_path)
    memory, _ = manager.remember(
        "Redstone uses Obsidian for readable memories.", project="redstone"
    )
    assert adapter.export().exported == 1
    path = next((adapter.vault / "Memories").rglob("*.md"))
    assert memory.id in path.read_text(encoding="utf-8")
    assert adapter.sync().unchanged == 1
    archived = manager.archive(memory.id)
    archive_path = adapter.archive_memory(archived)
    assert archive_path is not None and archive_path.parent.name == "Archive"
    assert archive_path.is_file()


def test_sync_imports_single_sided_obsidian_edit(tmp_path: Path) -> None:
    manager, adapter = build_adapter(tmp_path)
    memory, _ = manager.remember("Initial human-readable content.")
    adapter.export()
    path = next((adapter.vault / "Memories").rglob("*.md"))
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "Initial human-readable content.", "Human vault edit."
        ),
        encoding="utf-8",
    )
    report = adapter.sync()
    assert report.imported == 1
    assert manager.store.get(memory.id).content == "Human vault edit."


def test_sync_exports_single_sided_redstone_edit(tmp_path: Path) -> None:
    manager, adapter = build_adapter(tmp_path)
    memory, _ = manager.remember("Original SQLite content.")
    adapter.export()
    changed = memory.model_copy(
        update={
            "content": "SQLite changed content.",
            "summary": "SQLite changed content.",
            "version": 2,
        }
    )
    manager.store.save(changed)
    report = adapter.sync()
    assert report.exported == 1
    assert "SQLite changed content." in next((adapter.vault / "Memories").rglob("*.md")).read_text(
        encoding="utf-8"
    )


def test_sync_records_conflict_when_both_sides_change(tmp_path: Path) -> None:
    manager, adapter = build_adapter(tmp_path)
    memory, _ = manager.remember("Original content.")
    adapter.export()
    path = next((adapter.vault / "Memories").rglob("*.md"))
    path.write_text(
        path.read_text(encoding="utf-8").replace("Original content.", "Vault change."),
        encoding="utf-8",
    )
    manager.store.save(
        memory.model_copy(
            update={"content": "SQLite change.", "summary": "SQLite change.", "version": 2}
        )
    )
    report = adapter.sync()
    assert report.conflicts == 1
    assert (adapter.vault / "Conflicts" / f"{memory.id}-conflict.md").is_file()
    assert manager.store.get(memory.id).content == "SQLite change."


def test_import_skips_untrusted_or_non_redstone_files(tmp_path: Path) -> None:
    manager, adapter = build_adapter(tmp_path)
    adapter.initialize_vault()
    (adapter.vault / "ordinary.md").write_text("# Not a memory", encoding="utf-8")
    (adapter.vault / "malformed.md").write_text("---\nredstone_id: bad\n---\n", encoding="utf-8")
    memory, _ = manager.remember("Safe content.")
    text = memory_to_markdown(memory).replace("Safe content.", "password=unacceptablylongsecret")
    (adapter.vault / "unsafe.md").write_text(text, encoding="utf-8")
    report = adapter.import_vault()
    assert report.imported == 0
    assert report.skipped >= 3
