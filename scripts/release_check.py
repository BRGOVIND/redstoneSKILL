"""Build and validate Redstone from an installed wheel in a fresh environment."""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.1.0"


def run(command: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def executable(environment: Path, name: str) -> Path:
    scripts = environment / ("Scripts" if sys.platform == "win32" else "bin")
    suffix = ".exe" if sys.platform == "win32" else ""
    return scripts / f"{name}{suffix}"


def inspect_archives(wheel: Path, sdist: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        wheel_files = set(archive.namelist())
    required_wheel_suffixes = (
        "redstone/cli.py",
        "redstone/mcp/server.py",
        "share/redstone/skill/redstone-memory/SKILL.md",
        ".dist-info/METADATA",
    )
    for suffix in required_wheel_suffixes:
        if not any(name.endswith(suffix) for name in wheel_files):
            raise SystemExit(f"wheel missing required file: {suffix}")
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_files = archive.getnames()
    for suffix in (
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "SECURITY.md",
        "benchmark/run.py",
        "scripts/release_check.py",
    ):
        if not any(name.endswith(suffix) for name in sdist_files):
            raise SystemExit(f"sdist missing required file: {suffix}")


def main() -> int:
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "pytest", "-q"])
    with tempfile.TemporaryDirectory(prefix="redstone-release-") as directory:
        temporary = Path(directory)
        artifacts = temporary / "artifacts"
        run([sys.executable, "-m", "build", "--outdir", str(artifacts)])
        wheel = next(artifacts.glob("*.whl"))
        sdist = next(artifacts.glob("*.tar.gz"))
        inspect_archives(wheel, sdist)

        environment = temporary / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = executable(environment, "python")
        redstone = executable(environment, "redstone")
        run([str(python), "-m", "pip", "install", str(wheel)])
        version = run(
            [
                str(python),
                "-c",
                "from importlib.metadata import version; print(version('redstone-memory'))",
            ]
        ).strip()
        if version != EXPECTED_VERSION:
            raise SystemExit(f"installed version {version} != {EXPECTED_VERSION}")

        workspace = temporary / "workspace"
        run([str(redstone), "--root", str(workspace), "init"])
        doctor = json.loads(run([str(redstone), "--root", str(workspace), "doctor", "--json"]))
        failures = [item for item in doctor if item["status"] == "FAIL"]
        if failures:
            raise SystemExit("installed-package doctor reported a failure")
        run([str(redstone), "--root", str(workspace), "smoke-test"])
        run([str(redstone), "--root", str(workspace), "skill", "build"])
        benchmark = subprocess.run(
            [str(redstone), "--root", str(workspace), "benchmark", "core"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        expected = "Benchmarks require a Redstone source checkout"
        if benchmark.returncode != 2 or expected not in benchmark.stderr:
            raise SystemExit("installed-package benchmark boundary check failed")

    print("PASS release check: Ruff, tests, archives, clean install, doctor, smoke, Skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
