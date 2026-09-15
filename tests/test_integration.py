import hashlib
import json
from pathlib import Path

from redstone.cli import main
from redstone.config import RedstoneConfig
from redstone.core.manager import MemoryManager
from redstone.integration import build_skill_package, run_doctor, run_smoke_test, validate_skill
from redstone.mcp.server import TOOLS, handle_request
from redstone.storage.sqlite import SQLiteMemoryStore


def call_mcp_store(manager: MemoryManager, content: str, source: str, **extra: str) -> dict:
    response = handle_request(
        {
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "memory_store",
                "arguments": {
                    "content": content,
                    "project": "atlas",
                    "source": source,
                    **extra,
                },
            },
        },
        manager,
    )
    return response["result"]["structuredContent"]


def test_init_is_idempotent_and_doctor_supports_json(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "init"]) == 0
    assert main(["--root", str(tmp_path), "init"]) == 0
    output = capsys.readouterr().out
    assert "created" in output and "reused" in output
    assert main(["--root", str(tmp_path), "doctor", "--json"]) == 0
    checks = json.loads(capsys.readouterr().out)
    assert any(item["component"] == "sqlite" and item["status"] == "PASS" for item in checks)
    assert any(item["component"] == "obsidian" and item["status"] == "WARN" for item in checks)


def test_doctor_fails_before_init_without_writing(tmp_path: Path) -> None:
    checks = run_doctor(tmp_path)
    assert checks[-1].status == "FAIL"
    assert not (tmp_path / ".redstone").exists()


def test_memory_command_reports_uninitialized_workspace(tmp_path: Path, capsys) -> None:
    assert main(["--root", str(tmp_path), "recall", "prior decision"]) == 2
    assert "redstone init" in capsys.readouterr().err.lower()
    assert not (tmp_path / ".redstone").exists()


def test_configured_missing_obsidian_vault_fails_doctor(tmp_path: Path) -> None:
    main(["--root", str(tmp_path), "init"])
    config = tmp_path / ".redstone" / "config.toml"
    config.write_text(
        config.read_text().replace(
            'enabled = false\nvault_path = ""', 'enabled = true\nvault_path = "missing-vault"'
        ),
        encoding="utf-8",
    )
    checks = run_doctor(tmp_path)
    assert any(item.component == "obsidian" and item.status == "FAIL" for item in checks)


def test_mcp_dispatcher_runs_initialize_list_store_and_recall(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    initialized = handle_request({"id": 1, "method": "initialize"}, manager)
    listed = handle_request({"id": 2, "method": "tools/list"}, manager)
    stored = handle_request(
        {
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_store",
                "arguments": {
                    "content": "Atlas uses PostgreSQL.",
                    "project": "atlas",
                    "source": "session-1",
                },
            },
        },
        manager,
    )
    recalled = handle_request(
        {
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "memory_recall",
                "arguments": {"query": "What does Atlas use?", "project": "atlas"},
            },
        },
        manager,
    )
    assert initialized["result"]["serverInfo"]["name"] == "redstone"
    assert len(listed["result"]["tools"]) == len(TOOLS)
    assert listed["result"]["tools"][0]["inputSchema"]["type"] == "object"
    assert stored["result"]["structuredContent"]["created"]
    assert "PostgreSQL" in recalled["result"]["structuredContent"]["context"]
    assert handle_request({"method": "notifications/initialized"}, manager) is None


def test_mcp_store_can_preserve_superseded_history(tmp_path: Path) -> None:
    manager = MemoryManager(SQLiteMemoryStore(tmp_path / "index.db"))
    first = call_mcp_store(manager, "Atlas used PostgreSQL.", "session-1")
    second = call_mcp_store(
        manager,
        "Atlas now uses SQLite.",
        "session-3",
        supersedes=first["id"],
    )
    older = manager.store.get(first["id"])
    newer = manager.store.get(second["id"])
    assert older.superseded_by == newer.id
    assert newer.supersedes == older.id


def test_smoke_test_covers_memory_mcp_obsidian_and_security() -> None:
    result = run_smoke_test()
    assert all(result["mcp"].values())
    assert all(result["memory"].values())
    assert all(result["obsidian"].values())
    assert all(result["security"].values())
    assert all(result["skill"].values())


def test_skill_validation_and_build_are_deterministic(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "skill" / "redstone-memory"
    assert validate_skill(source)[0]
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    build_skill_package(source, first)
    build_skill_package(source, second)
    assert (
        hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    )


def test_configuration_exposes_single_runtime_paths(tmp_path: Path) -> None:
    main(["--root", str(tmp_path), "init"])
    config = RedstoneConfig.load(tmp_path)
    assert config.database_path == Path(".redstone/index.db")
    assert config.mcp_enabled
    assert config.skill_package_path == Path("dist/redstone-memory.zip")
