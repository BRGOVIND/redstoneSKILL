# Redstone

Local-first persistent memory infrastructure for AI agents.

> **Your Memories. Your Vault. Your Machine.**

Redstone stores typed, provenance-aware memories in SQLite, keeps retrieval
explainable, blocks obvious credentials, and treats all recalled memory as
untrusted data. It works offline without an embedding provider.

Obsidian is an optional human-readable mirror. SQLite remains Redstone's
source of truth; synchronization detects two-sided edits and records conflicts
instead of overwriting either side.

## Architecture

```text
Claude / AI client
        |
      Skill
        |
       MCP
        |
    Redstone
     /     \
 SQLite   Obsidian
```

SQLite is the authoritative structured state. Obsidian is an optional
human-readable mirror. MCP provides local tool access, while the Skill tells a
client when to store and retrieve durable information. Memory and imported
Markdown are untrusted data; their contents are never executable instructions.

## Features

- Typed memories with deterministic IDs, confidence, importance, and provenance
- Temporal history, explicit supersession, and unresolved-conflict preservation
- Explainable lexical, adaptive, and relationship-aware retrieval
- Bounded context construction with current, historical, and timeline intent
- SQLite persistence and conflict-aware Obsidian synchronization
- Provider-neutral local MCP server and packaged Claude Skill
- Secret filtering and instruction-like-memory isolation
- Offline core operation and deterministic synthetic/authored benchmarks

## Quick start

```bash
python -m pip install .
redstone init
redstone doctor
redstone smoke-test
redstone remember "Redstone uses local SQLite storage" --project redstone
redstone search "local storage" --project redstone
redstone recall "What storage did we choose?" --project redstone
```

## Obsidian

```bash
redstone obsidian init ~/Documents/Redstone-Vault
redstone obsidian export
redstone obsidian sync
```

See [Obsidian guide](docs/guides/obsidian.md) and
[sync architecture](docs/architecture/obsidian-sync.md).

## MCP and Claude

Start local stdio transport with `redstone mcp`. Configure a client to run
`redstone mcp` in your Redstone workspace. Tools include search, recall, store,
update, archive, related memories, timeline, conflicts, and stats. Claude skill
instructions live in `skill/redstone-memory/`. See [MCP guide](docs/guides/mcp.md).
Package it with `redstone skill build`.

`redstone init` is idempotent. `doctor` validates configuration, SQLite,
privacy, MCP, Skill assets, and optional Obsidian state without changing user
data. `smoke-test` uses a disposable workspace and writes
`benchmark/reports/integration-latest.md`.

For real Claude Code registration, packaged Skill installation, isolated test
prompts, and honest live-validation boundaries, see the
[live Claude validation guide](docs/guides/live-claude-validation.md).

## Benchmark

Run deterministic hard RMB retrieval evaluation:

```bash
redstone benchmark
```

Benchmark commands require a source checkout. Runtime wheels intentionally omit
benchmark datasets and reports; source distributions and the repository include
them for reproducibility.

Results write to `benchmark/results/latest.json` and
`benchmark/reports/latest.md`. Answer-level results write to
`benchmark/results/answer-latest.json` and
`benchmark/reports/answer-latest.md`. Results are measured, never claimed in
advance.
On Redstone's synthetic Phase 9 RMB run, the dataset contains 220 conversations and 72 questions,
including 22 multi-memory questions. Raw lexical top-1 recall is 61.11%, fixed
Redstone top-1 recall is 83.33%, and coverage-aware adaptive recall is 100.00%.
Adaptive retrieval selects 1.60 memories and uses 24.0 context tokens per
question on average. See [benchmark methodology](docs/benchmark.md). RMB is a
synthetic retrieval benchmark, not proof of general AI memory improvement.

Phase 10 adds an authored answer-level workload: 10 projects, 100 sessions, and
110 grounded questions. It compares equal-budget recent conversation history
against Redstone adaptive context using a provider-independent answer interface
and deterministic extractive provider. This validates evaluation plumbing and
failure attribution; it does not measure open-ended LLM reasoning.

On the Phase 10 authored answer-evaluation workload, recent-history baseline accuracy is
65.45%; Redstone answer accuracy is 100.00%, a measured gain of 34.55 percentage
points. Redstone uses 120.8 versus 162.8 context tokens on average, a 25.82%
reduction. These numbers apply only to this deterministic synthetic workload.

Phase 11 adds deterministic robustness evaluation for temporal conflicts,
contradictions, similar entities, keyword distractors, duplicates, incomplete
and unsupported evidence, provenance, multi-memory questions, and adversarial
instruction-like memory content:

```bash
redstone benchmark robustness
```

The authored-v1 robustness dataset contains 10 projects, 160 sessions, 150
stored memories, and 130 questions. Measured answer accuracy is 62.31% for the
equal-budget recent-history baseline and 100.00% for Redstone. See the
[robustness report](benchmark/reports/robustness-latest.md). These synthetic
results do not establish general real-world or LLM performance.

Phase 12 adds a provider-neutral long-context evaluation with 10 synthetic
projects, 400 sessions, 400 authored facts, and 120 questions. Offline mode is
reproducible:

```bash
redstone benchmark llm
```

It separates equal-budget recent-history versus retrieval context from a
full-history ablation, and writes `llm-latest`, `llm-long-context`, and failure
reports. On the deterministic Phase 12 long-context workload, equal-budget
baseline accuracy is 8.33%, equal-budget Redstone accuracy is 83.33%, and the
full-history baseline reaches 91.67%. This demonstrates context efficiency at
equal budget, not superiority over full history. To run same-provider OpenAI
generation, set `OPENAI_API_KEY` and
`REDSTONE_LLM_MODEL` only in environment, then run
`redstone benchmark llm --provider openai --runs 3 --max-questions 20`.
Credentials are never written to results. Offline results validate evaluation
plumbing, not open-ended LLM quality.

Phase 13 investigates optional semantic candidate retrieval without changing
default lexical behavior:

```bash
redstone benchmark semantic
```

It compares lexical, semantic, and hybrid retrieval on 50 paraphrase-targeted
questions, caches vectors locally in SQLite, and records an explicit decision
in `benchmark/reports/semantic-latest.md`: semantic retrieval was evaluated and
was not adopted as the default.

Phase 14 evaluates deterministic memory lifecycle stability across 20 projects,
1,100 candidates, and 500 questions:

```bash
redstone benchmark lifecycle
```

Candidate formation rejects only obvious conversational noise before existing
privacy checks. Exact duplicates collapse; near-duplicates, contradictions, and
superseded historical states remain preserved. Reports include growth,
retrieval stability, restart integrity, and Obsidian round-trip integrity.

Phase 15 adds deterministic temporal/conflict composition:

```bash
redstone benchmark temporal
```

It reconstructs bounded supersession chains, derives current/date-effective
state, distinguishes resolved and unresolved conflicts, keeps entity-scoped
differences separate, and emits provenance-preserving temporal context.

## Privacy

Redstone is local-first. It blocks obvious secrets before persistence and treats
retrieved memory and imported Markdown as untrusted data. It never executes
memory content.

See [the implementation plan](docs/architecture/REDSTONE_IMPLEMENTATION_PLAN.md).

## Limitations

Lexical retrieval remains the default. Redstone has no LLM memory consolidation,
cloud memory backend, or web/mobile UI. Benchmarks are synthetic or authored and
do not establish universal real-world performance. Live Claude model validation
remains `NOT RUN` because external client/API attempts failed before inference;
local MCP and Skill validation must not be interpreted as a Claude compatibility
claim.

See [documentation index](docs/README.md), [security policy](SECURITY.md), and
[contribution guide](CONTRIBUTING.md).
