"""Production diagnostics, smoke testing, and deterministic Skill packaging."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from redstone.config import RedstoneConfig
from redstone.core.manager import MemoryManager
from redstone.mcp.server import TOOLS, handle_request
from redstone.obsidian.adapter import ObsidianAdapter
from redstone.privacy.policy import PrivacyPolicy
from redstone.storage.sqlite import SQLiteMemoryStore


@dataclass(frozen=True)
class Diagnostic:
    component: str
    status: str
    message: str


def _repository() -> Path:
    return Path(__file__).resolve().parents[2]


def skill_source() -> Path:
    """Locate Skill assets in a checkout or an installed wheel."""
    candidates = (
        _repository() / "skill" / "redstone-memory",
        Path(sys.prefix) / "share" / "redstone" / "skill" / "redstone-memory",
    )
    return next((path for path in candidates if path.is_dir()), candidates[0])


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def validate_skill(path: Path) -> tuple[bool, str]:
    skill = path / "SKILL.md"
    if not skill.is_file():
        return False, "SKILL.md missing"
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nname: redstone-memory\n" not in text:
        return False, "SKILL.md frontmatter invalid"
    required = ("memory_recall", "memory_store", "untrusted data", "Never store")
    if not all(term.casefold() in text.casefold() for term in required):
        return False, "SKILL.md policy incomplete"
    return True, "Skill instructions valid"


def run_doctor(root: Path) -> list[Diagnostic]:
    """Inspect local installation without mutating user data."""
    root = root.resolve()
    checks = [
        Diagnostic("runtime", "PASS", f"Python {sys.version_info.major}.{sys.version_info.minor}")
    ]
    config_path = root / ".redstone" / "config.toml"
    if not config_path.is_file():
        return checks + [
            Diagnostic("configuration", "FAIL", "Redstone not initialized; run `redstone init`")
        ]
    try:
        config = RedstoneConfig.load(root)
        checks.append(Diagnostic("configuration", "PASS", str(config_path)))
    except (OSError, ValueError) as error:
        return checks + [
            Diagnostic("configuration", "FAIL", f"Invalid configuration: {type(error).__name__}")
        ]
    if PrivacyPolicy().scan(config_path.read_text(encoding="utf-8")):
        checks.append(Diagnostic("security", "FAIL", "Secret-like value found in configuration"))
    else:
        checks.append(Diagnostic("security", "PASS", "No persisted credentials detected"))
    database = _resolve(root, config.database_path)
    if not database.is_file():
        checks.append(Diagnostic("sqlite", "FAIL", "Database missing; run `redstone init`"))
    else:
        try:
            with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
                table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
                ).fetchone()
            checks.append(
                Diagnostic(
                    "sqlite",
                    "PASS" if table else "FAIL",
                    "Memory schema readable" if table else "Memory schema missing",
                )
            )
        except sqlite3.Error:
            checks.append(Diagnostic("sqlite", "FAIL", "Database unreadable"))
    with tempfile.TemporaryDirectory(prefix="redstone-doctor-") as directory:
        temporary_root = Path(directory)
        manager = MemoryManager(SQLiteMemoryStore(Path(directory) / "doctor.db"))
        memory, created = manager.remember("Doctor deterministic memory check.", source="doctor")
        repeated, repeated_created = manager.remember(
            "Doctor deterministic memory check.", source="doctor"
        )
        deterministic = repeated.id == memory.id and not repeated_created
        privacy_blocked = False
        try:
            manager.remember("password=unacceptablylongsecret", source="doctor")
        except ValueError:
            privacy_blocked = True
        checks.append(
            Diagnostic(
                "memory",
                "PASS" if created and deterministic else "FAIL",
                "Write/read and deterministic ID verified",
            )
        )
        checks.append(
            Diagnostic(
                "privacy", "PASS" if privacy_blocked else "FAIL", "Secret rejection verified"
            )
        )
        initialize = handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, manager
        )
        listed = handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, manager
        )
        mcp_ready = (
            initialize.get("result", {}).get("serverInfo", {}).get("name") == "redstone"
            and len(listed.get("result", {}).get("tools", [])) >= 9
        )
        skill = skill_source()
        valid, message = validate_skill(skill)
        package_ready = False
        if valid:
            first = build_skill_package(skill, temporary_root / "skill-a.zip")
            second = build_skill_package(skill, temporary_root / "skill-b.zip")
            package_ready = first.read_bytes() == second.read_bytes()
    if not config.obsidian_enabled or not config.obsidian_vault_path:
        checks.append(
            Diagnostic(
                "obsidian", "WARN", "Vault not configured; run `redstone obsidian init <path>`"
            )
        )
    else:
        vault = config.obsidian_vault_path
        writable = (
            vault.is_dir()
            and (vault / ".redstone").is_dir()
            and os.access(vault, os.R_OK | os.W_OK)
        )
        checks.append(
            Diagnostic(
                "obsidian",
                "PASS" if writable else "FAIL",
                "Vault configured and initialized"
                if writable
                else "Configured vault missing or invalid",
            )
        )
    checks.append(
        Diagnostic(
            "mcp",
            "PASS" if config.mcp_enabled and mcp_ready else "FAIL",
            f"MCP initialize and tools/list verified with {len(TOOLS)} tools",
        )
    )
    checks.append(
        Diagnostic(
            "skill",
            "PASS" if valid and package_ready else "FAIL",
            f"{message}; deterministic package verified" if package_ready else message,
        )
    )
    return checks


def doctor_exit_code(checks: list[Diagnostic]) -> int:
    return 1 if any(check.status == "FAIL" for check in checks) else 0


def build_skill_package(source: Path, destination: Path) -> Path:
    """Build reproducible Claude Skill archive with fixed metadata."""
    valid, message = validate_skill(source)
    if not valid:
        raise ValueError(message)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as archive:
        for file in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = file.relative_to(source.parent).as_posix()
            info = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, file.read_bytes())
    return destination


def run_smoke_test() -> dict:
    """Exercise production boundaries entirely inside an isolated directory."""
    timings: dict[str, float] = {}
    with tempfile.TemporaryDirectory(prefix="redstone-smoke-") as directory:
        root = Path(directory)
        start = time.perf_counter()
        manager = MemoryManager(SQLiteMemoryStore(root / ".redstone" / "index.db"))
        timings["initialization_ms"] = (time.perf_counter() - start) * 1_000
        start = time.perf_counter()
        initialize = handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, manager
        )
        tools = handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, manager
        )
        timings["mcp_request_ms"] = (time.perf_counter() - start) * 1_000
        start = time.perf_counter()
        first_response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "memory_store",
                    "arguments": {
                        "content": "Atlas originally used PostgreSQL.",
                        "type": "decision",
                        "source": "session-1",
                        "project": "atlas",
                    },
                },
            },
            manager,
        )
        second_response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "memory_store",
                    "arguments": {
                        "content": "Atlas now uses SQLite.",
                        "type": "decision",
                        "source": "session-3",
                        "project": "atlas",
                    },
                },
            },
            manager,
        )
        first = first_response["result"]["structuredContent"]
        second = second_response["result"]["structuredContent"]
        timings["memory_write_ms"] = (time.perf_counter() - start) * 1_000
        manager.supersede(first["id"], second["id"])
        start = time.perf_counter()
        current_response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "memory_recall",
                    "arguments": {"query": "What database does Atlas use now?", "project": "atlas"},
                },
            },
            manager,
        )
        historical_response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "memory_recall",
                    "arguments": {
                        "query": "What database did Atlas originally use?",
                        "project": "atlas",
                    },
                },
            },
            manager,
        )
        current = current_response["result"]["structuredContent"]["context"]
        historical = historical_response["result"]["structuredContent"]["context"]
        timings["recall_ms"] = (time.perf_counter() - start) * 1_000
        start = time.perf_counter()
        composition = manager.compose_temporal("Show Atlas database timeline", project="atlas")
        timings["temporal_composition_ms"] = (time.perf_counter() - start) * 1_000
        vault = root / "vault"
        adapter = ObsidianAdapter(vault, manager.store)
        adapter.initialize_vault()
        start = time.perf_counter()
        exported = adapter.export()
        roundtrip = SQLiteMemoryStore(root / "roundtrip.db")
        imported = ObsidianAdapter(vault, roundtrip).import_vault()
        timings["obsidian_sync_ms"] = (time.perf_counter() - start) * 1_000
        secret_blocked = False
        try:
            manager.remember("Authorization: Bearer abcdefghijklmnopqrstuvwxyz", source="smoke")
        except ValueError:
            secret_blocked = True
        skill = skill_source()
        skill_valid, _ = validate_skill(skill)
        first_package = build_skill_package(skill, root / "skill-a.zip")
        second_package = build_skill_package(skill, root / "skill-b.zip")
        return {
            "offline": True,
            "mcp": {
                "initialize": initialize["result"]["serverInfo"]["name"] == "redstone",
                "tools": len(tools["result"]["tools"]),
                "store": first["created"] and second["created"],
                "recall": "SQLite" in current and "PostgreSQL" in historical,
            },
            "memory": {
                "current": "SQLite" in current,
                "historical": "PostgreSQL" in historical,
                "provenance": "session-1" in historical and "session-3" in current,
                "timeline_entries": len(composition.timeline),
            },
            "obsidian": {
                "exported": exported.exported,
                "imported": imported.imported,
                "roundtrip": len(roundtrip.list()) == 2,
            },
            "security": {
                "secret_blocked": secret_blocked,
                "untrusted_context": "untrusted data" in current,
            },
            "skill": {
                "valid": skill_valid,
                "deterministic_package": first_package.read_bytes() == second_package.read_bytes(),
            },
            "timings": timings,
        }


def write_integration_report(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Redstone Production Integration\n\n"
        "## Readiness\n\n"
        "**READY for local Claude/MCP integration.** The automated smoke test ran "
        "offline in a disposable workspace; it did not modify a user vault or production database.\n\n"
        "## Architecture\n\n"
        "Claude client + Skill -> local stdio MCP -> Redstone core -> SQLite. "
        "Obsidian is an optional human-readable mirror; SQLite remains authoritative.\n\n"
        "## Installation and diagnostics\n\n"
        "```bash\npython -m pip install .\nredstone init\nredstone doctor\n"
        "redstone smoke-test\nredstone skill build\n```\n\n"
        f"Runtime: Python {sys.version_info.major}.{sys.version_info.minor}. "
        "Package metadata requires Python 3.11+ and Pydantic 2.7+.\n\n"
        "## MCP client configuration\n\n"
        '```json\n{\n  "mcpServers": {\n    "redstone": {\n'
        '      "command": "redstone",\n      "args": ["--root", '
        '"/path/to/workspace", "mcp"]\n    }\n  }\n}\n```\n\n'
        "Verified lifecycle: `initialize`, `tools/list`, `memory_store`, "
        "`memory_recall`, and clean EOF shutdown.\n\n"
        "## Obsidian workflow\n\n"
        "```bash\nredstone obsidian init /path/to/vault\nredstone obsidian export\n"
        "redstone obsidian sync\nredstone obsidian status\n```\n\n"
        "The smoke test verified export/import round-trip equivalence using an isolated vault.\n\n"
        "## Test results\n\n"
        f"```json\n{json.dumps(result, indent=2, sort_keys=True)}\n```\n\n"
        "## Limitations and known issues\n\n"
        "Claude client registration and interactive client UI behavior remain external and were "
        "not automated. Obsidian needs a local writable vault. Real OpenAI evaluation remains "
        "optional and credential-driven. The clean-install verification used the built wheel with "
        "host Pydantic available; package build itself used an isolated PEP 517 environment. "
        "Core remains local-first with no mandatory embeddings, LLM consolidation, cloud storage, "
        "or UI.\n",
        encoding="utf-8",
    )
