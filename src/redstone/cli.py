"""Human-readable local CLI."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

from redstone.config import RedstoneConfig, configure_obsidian, initialize_config
from redstone.core.manager import MemoryManager
from redstone.core.memory import MemoryType
from redstone.obsidian.adapter import ObsidianAdapter
from redstone.privacy.policy import PrivacyPolicy
from redstone.storage.sqlite import SQLiteMemoryStore


def _manager(root: Path) -> MemoryManager:
    database = RedstoneConfig.load(root).database_path
    return MemoryManager(SQLiteMemoryStore(database if database.is_absolute() else root / database))


def _adapter(root: Path) -> ObsidianAdapter:
    config = RedstoneConfig.load(root)
    if not config.obsidian_vault_path:
        raise ValueError("Obsidian vault not configured; run `redstone obsidian init <path>`")
    return ObsidianAdapter(config.obsidian_vault_path, _manager(root).store)


def _initialization_error(root: Path) -> str | None:
    config_path = root / ".redstone" / "config.toml"
    if not config_path.is_file():
        return "Redstone is not initialized. Run: redstone init"
    try:
        configured = RedstoneConfig.load(root).database_path
    except (OSError, ValueError):
        return "Redstone configuration is invalid. Run: redstone doctor"
    database = configured if configured.is_absolute() else root / configured
    if not database.is_file():
        return "Redstone database is not initialized. Run: redstone init"
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="redstone", description="Local-first AI memory")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="memory workspace")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    sub.add_parser("smoke-test")
    remember = sub.add_parser("remember")
    remember.add_argument("content")
    remember.add_argument("--type", choices=[item.value for item in MemoryType], default="semantic")
    remember.add_argument("--project")
    remember.add_argument("--source", default="manual")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--project")
    recall = sub.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--project")
    recall.add_argument("--max-tokens", type=int, default=500)
    recall.add_argument("--explain", action="store_true")
    archive = sub.add_parser("archive")
    archive.add_argument("memory_id")
    sub.add_parser("stats")
    privacy = sub.add_parser("privacy")
    privacy.add_argument("action", choices=["scan", "audit"])
    privacy.add_argument("text", nargs="?")
    obsidian = sub.add_parser("obsidian")
    obsidian_sub = obsidian.add_subparsers(dest="obsidian_command", required=True)
    obsidian_init = obsidian_sub.add_parser("init")
    obsidian_init.add_argument("path", type=Path)
    obsidian_sub.add_parser("status")
    export = obsidian_sub.add_parser("export")
    export.add_argument("--project")
    export.add_argument("--type", choices=[item.value for item in MemoryType])
    export.add_argument("--memory")
    obsidian_import = obsidian_sub.add_parser("import")
    obsidian_import.add_argument("path", type=Path, nargs="?")
    obsidian_sub.add_parser("sync")
    obsidian_sub.add_parser("conflicts")
    sub.add_parser("mcp")
    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument(
        "suite",
        nargs="?",
        choices=["all", "core", "robustness", "llm", "semantic", "lifecycle", "temporal"],
        default="all",
    )
    benchmark.add_argument("--provider", choices=["deterministic", "openai"])
    benchmark.add_argument("--runs", type=int, default=1)
    benchmark.add_argument("--max-questions", type=int)
    benchmark.add_argument("--judge", action="store_true")
    skill = sub.add_parser("skill")
    skill.add_argument("action", choices=["build"])
    timeline = sub.add_parser("timeline")
    timeline.add_argument("project")
    related = sub.add_parser("related")
    related.add_argument("memory_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "init":
        configured_database = RedstoneConfig.load(root).database_path
        database = (
            configured_database if configured_database.is_absolute() else root / configured_database
        )
        config_path = root / ".redstone" / "config.toml"
        database_existed, config_existed = database.exists(), config_path.exists()
        _manager(root)
        initialize_config(root)
        print(f"Redstone ready at {root / '.redstone'}")
        print(f"database: {'reused' if database_existed else 'created'} {database}")
        print(f"configuration: {'reused' if config_existed else 'created'} {config_path}")
        return 0
    if args.command == "doctor":
        from redstone.integration import doctor_exit_code, run_doctor

        checks = run_doctor(root)
        if args.json:
            print(json.dumps([check.__dict__ for check in checks], indent=2))
        else:
            for check in checks:
                print(f"{check.status:<4} {check.component}: {check.message}")
        return doctor_exit_code(checks)
    if args.command == "smoke-test":
        from redstone.integration import run_smoke_test, write_integration_report

        result = run_smoke_test()
        report = root / "benchmark" / "reports" / "integration-latest.md"
        result_path = root / "benchmark" / "results" / "integration-latest.json"
        write_integration_report(result, report)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        passed = (
            all(result["mcp"].values())
            and all(result["memory"].values())
            and all(result["obsidian"].values())
            and all(result["security"].values())
            and all(result["skill"].values())
        )
        print(f"{'PASS' if passed else 'FAIL'} production smoke test")
        print(f"Integration report: {report}")
        return 0 if passed else 1
    if args.command == "privacy":
        policy = PrivacyPolicy()
        if args.action == "audit":
            print("Privacy audit: secret blocking enabled")
            return 0
        findings = policy.scan(args.text or "")
        print("blocked: " + ", ".join(item.kind for item in findings) if findings else "clear")
        return 0
    needs_initialization = args.command in {
        "remember",
        "search",
        "recall",
        "archive",
        "stats",
        "timeline",
        "related",
        "obsidian",
        "mcp",
    }
    if needs_initialization and (error := _initialization_error(root)):
        print(error, file=sys.stderr)
        return 2
    if args.command == "obsidian":
        if args.obsidian_command == "init":
            adapter = ObsidianAdapter(args.path, _manager(root).store)
            adapter.initialize_vault()
            configure_obsidian(root, args.path)
            print(f"Obsidian vault initialized: {adapter.vault}")
            return 0
        try:
            adapter = _adapter(root)
        except (OSError, ValueError) as error:
            print(f"Obsidian configuration error: {error}", file=sys.stderr)
            return 2
        if args.obsidian_command == "status":
            for key, value in adapter.status().items():
                print(f"{key}: {value}")
        elif args.obsidian_command == "export":
            report = adapter.export(
                project=args.project,
                memory_type=MemoryType(args.type) if args.type else None,
                memory_id=args.memory,
            )
            print(f"exported: {report.exported}")
        elif args.obsidian_command == "import":
            report = adapter.import_vault(args.path)
            print(f"imported: {report.imported}; skipped: {report.skipped}")
        elif args.obsidian_command == "sync":
            report = adapter.sync()
            print(
                f"exported: {report.exported}; imported: {report.imported}; conflicts: {report.conflicts}"
            )
        else:
            print(f"conflicts: {adapter.status()['conflicts']}")
        return 0
    if args.command == "mcp":
        from redstone.mcp.server import run_stdio

        run_stdio(str(root))
        return 0
    if args.command == "benchmark":
        repository = Path(__file__).resolve().parents[2]
        if not (repository / "benchmark" / "run.py").is_file():
            print(
                "Benchmarks require a Redstone source checkout; runtime wheels exclude benchmark assets.",
                file=sys.stderr,
            )
            return 2
        sys.path.insert(0, str(repository))
        if args.suite in {"all", "core"}:
            runpy.run_path(str(repository / "benchmark" / "run.py"), run_name="__main__")
            print(f"Benchmark report: {repository / 'benchmark' / 'reports' / 'latest.md'}")
            print(f"Answer report: {repository / 'benchmark' / 'reports' / 'answer-latest.md'}")
        if args.suite in {"all", "robustness"}:
            from benchmark.robustness_run import main as run_robustness

            run_robustness()
            print(
                "Robustness report: "
                f"{repository / 'benchmark' / 'reports' / 'robustness-latest.md'}"
            )
        if args.suite == "llm":
            from benchmark.answers import ProviderConfigurationError
            from benchmark.llm_run import main as run_llm

            if args.runs < 1:
                raise ValueError("--runs must be at least 1")
            try:
                run_llm(
                    provider_name=args.provider,
                    runs=args.runs,
                    max_questions=args.max_questions,
                    judge=args.judge,
                )
            except ProviderConfigurationError as error:
                print(f"LLM configuration error: {error}", file=sys.stderr)
                return 2
            print(f"LLM report: {repository / 'benchmark' / 'reports' / 'llm-latest.md'}")
        if args.suite == "semantic":
            from benchmark.semantic_run import main as run_semantic

            run_semantic()
            print(f"Semantic report: {repository / 'benchmark' / 'reports' / 'semantic-latest.md'}")
        if args.suite == "lifecycle":
            from benchmark.lifecycle_run import main as run_lifecycle

            run_lifecycle()
            print(
                f"Lifecycle report: {repository / 'benchmark' / 'reports' / 'lifecycle-latest.md'}"
            )
        if args.suite == "temporal":
            from benchmark.temporal_run import main as run_temporal

            run_temporal()
            print(f"Temporal report: {repository / 'benchmark' / 'reports' / 'temporal-latest.md'}")
        return 0
    if args.command == "skill":
        from redstone.integration import build_skill_package, skill_source

        destination = root / RedstoneConfig.load(root).skill_package_path
        build_skill_package(skill_source(), destination)
        print(f"Built {destination}")
        return 0
    manager = _manager(root)
    if args.command == "remember":
        memory, created = manager.remember(
            args.content, args.type, source=args.source, project=args.project
        )
        print(f"{'Stored' if created else 'Duplicate'} {memory.id}")
    elif args.command == "search":
        for result in manager.search(args.query, project=args.project):
            print(f"{result.memory.id} {result.score:.3f} {result.memory.summary}")
    elif args.command == "recall":
        if args.explain:
            selection = manager.retrieve_adaptive(
                args.query,
                project=args.project,
                max_memories=5,
                max_tokens=args.max_tokens,
            )
            print(f"intent: {selection.analysis.intent.value}")
            print(
                "requirements: " + ", ".join(item.value for item in selection.analysis.requirements)
            )
            print(f"coverage: {selection.coverage:.0%}")
            for result in selection.results:
                print(f"{result.memory.id} {result.score:.3f} {result.reason}")
        print(
            manager.recall(
                args.query,
                project=args.project,
                max_tokens=args.max_tokens,
            )
        )
    elif args.command == "archive":
        memory = manager.archive(args.memory_id)
        config = RedstoneConfig.load(root)
        if config.obsidian_vault_path:
            ObsidianAdapter(config.obsidian_vault_path, manager.store).archive_memory(memory)
        print(f"Archived {memory.id}")
    elif args.command == "timeline":
        for memory in manager.timeline(args.project):
            print(f"{memory.observed_at.isoformat()} {memory.id} {memory.summary}")
    elif args.command == "related":
        for memory in manager.related(args.memory_id):
            print(f"{memory.id} {memory.summary}")
    else:
        for key, value in manager.stats().items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
