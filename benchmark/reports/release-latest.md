# Redstone v0.1.0 Release Readiness

## Release Verdict

**READY WITH WARNINGS**

The package, installed runtime, deterministic tests, release automation, MCP,
Skill, Obsidian, and security boundaries pass local release validation. Public
release is reasonable after the user establishes the intended Git repository
and reviews the files below. Live Claude inference and the first hosted CI run
remain outstanding external evidence.

## Repository

- Git state observed read-only: `redstone/` is wholly untracked inside its parent workspace repository.
- Parent branch: `master`; parent remote identifies an unrelated development-tooling repository.
- No Git mutation, staging, commit, configuration, or remote operation was performed.
- `.gitignore` now excludes virtual environments, caches, bytecode, databases,
  Redstone runtime state, release build output, benchmark runtime workspaces,
  local Claude/MCP state, environment files, keys, vaults, and logs.
- Intentional benchmark fixtures, JSON results, and Markdown reports remain visible.

## Package

| Check | Result |
| --- | --- |
| Name/version | `redstone-memory` 0.1.0 |
| Python | 3.11+; CI matrix 3.11, 3.12, 3.13 |
| Runtime dependency | Pydantic 2.7 to less than 3 |
| Build backend | setuptools |
| Wheel | PASS |
| Source distribution | PASS |
| `twine check` | PASS for both archives |
| Fresh virtual environment install | PASS |
| Installed metadata version | 0.1.0 |
| Wheel contents | CLI, core, MCP, metadata, license, and Skill assets present |
| Source contents | Runtime source, tests, benchmarks, reports, docs, and release checker present |

The first release-check run exposed a redundant license-classifier conflict
with current setuptools. Removing that classifier fixed the build while keeping
the SPDX `MIT` license expression and version unchanged.

## CI

`.github/workflows/ci.yml` installs and tests Python 3.11, 3.12, and 3.13,
runs Ruff and pytest, builds wheel/sdist, and runs the installed-package release
checker. It has read-only repository permissions and requires no model, Claude,
Anthropic, OpenAI, Obsidian, or cloud credentials. YAML parsing passed locally;
`actionlint` was unavailable and the workflow has not yet run on GitHub.

## CLI and Installed Runtime

The deterministic `scripts/release_check.py` orchestration passed from a fresh
environment: Ruff, pytest, isolated PEP 517 build, archive inspection, wheel
installation with dependencies, installed version check, `redstone init`, JSON
doctor, smoke test, Skill build, and clear source-checkout boundary for benchmark
commands from runtime-only wheels.

## MCP

MCP protocol initialize, notifications, tools/list schemas, structured tool
results, store, cross-process recall, supersession, temporal/current/historical
retrieval, provenance, and clean EOF shutdown are covered by tests and the
installed-package smoke path. Result: **PASS**.

## Skill

`SKILL.md` frontmatter/policy validation, changed-decision supersession guidance,
byte-identical deterministic archive builds, clean-install build, and wheel
asset inclusion passed. Result: **PASS**.

## Obsidian

Initialization, deterministic filenames, export, status, sync, archive,
single-sided edits, conflict preservation, privacy rejection, and
SQLite-to-Obsidian-to-SQLite round-trip tests passed. SQLite remains
authoritative. Result: **PASS**.

## Security

- Public-file scan found no credential-shaped values, personal user paths, or email addresses.
- Credential terms found in source/docs are policy logic, environment-variable names, and synthetic test examples.
- Secret-like memory is rejected before persistence.
- Retrieved and imported content remains untrusted data, not instructions.
- Instruction-like memory tests preserve data without executing instructions or deleting memories.
- The project makes no formal security-proof or universal secret-detection guarantee.

## Benchmarks

All claims are scoped to deterministic synthetic/authored workloads:

| Phase | Preserved result |
| --- | --- |
| 9 | Synthetic RMB adaptive recall 100% |
| 10 | Authored deterministic answer accuracy 100% |
| 11 | Authored robustness answer accuracy 100% |
| 12 | Equal-budget baseline 8.33%, Redstone 83.33%, full-history baseline 91.67% |
| 13 | Semantic default decision: **NO** |
| 14 | Persistence, privacy, provenance, restart, and sync integrity pass |
| 15 | Authored temporal/conflict composition accuracy 100% |
| 16 | Installed production integration smoke passes |
| 17 | Live Claude inference: **NOT RUN** |

Phase 12 supports a context-efficiency interpretation under equal budget; it
does not show superiority over full history. No benchmark establishes universal
model accuracy, hallucination elimination, or real-world Claude performance.

## Limitations

- Lexical retrieval is the default; evaluated semantic retrieval was not adopted.
- No LLM memory consolidation, cloud memory backend, or web/mobile UI.
- Live Claude inference validation remains `NOT RUN` after external failures before inference.
- Claude/other client registration and Skill installation remain client-dependent.
- Obsidian requires a writable local vault and is optional.
- Benchmark datasets are synthetic or authored; latency varies by machine.
- CI is configured and locally validated but has no hosted run yet.
- The project is not currently represented as its own tracked Git repository.

## Files Requiring User Review

Created: `.github/workflows/ci.yml`, `MANIFEST.in`, `scripts/release_check.py`,
`docs/README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
`benchmark/reports/release-latest.md`, and
`benchmark/results/release-latest.json`.

Modified: `.gitignore`, `pyproject.toml`, `README.md`, `SECURITY.md`,
`CHANGELOG.md`, `docs/benchmark.md`, `src/redstone/cli.py`, `benchmark/run.py`,
and `benchmark/reports/latest.md`.

## Release Recommendation

Review the release files, establish the intended Git boundary, then run the
first hosted CI workflow. If CI passes, v0.1.0 is ready for packaging/publication
with the documented live-Claude limitation retained.
