# Redstone Implementation Plan

## Current state

No Redstone repository exists in the inspected workspace. `../RedForge` is an
unrelated local AI engineering platform and is intentionally not reused. This
repository starts as an isolated Python 3.11+ package.

## Target architecture

The core is provider-independent and local-first. A typed memory manager
coordinates privacy filtering, SQLite persistence, a lightweight graph, and
transparent hybrid retrieval. Obsidian and MCP are adapters over that core;
embeddings are optional enhancements.

```text
CLI / MCP / Python API
        |
MemoryManager
  | storage | retrieval | graph | privacy | temporal
        |
SQLite + optional Obsidian vault + optional embedding provider
```

## Phases

1. Foundation: configuration, typed models, privacy filtering, SQLite store,
   deterministic IDs, keyword retrieval, CLI, and tests.
2. Obsidian: safe Markdown serialization, vault layout, export/import, and
   non-destructive synchronization.
3. Intelligent memory: hybrid ranking, temporal supersession, decay,
   deduplication, conflicts, and graph traversal.
4. Integration: MCP tools and distributable Claude skill.
5. RMB: deterministic dataset, baseline, evaluation, reports.
6. Hardening: path boundaries, prompt-injection handling, regression and
   integration coverage, documentation audit.

## Dependency graph

`models/config -> privacy/storage -> manager -> retrieval/CLI -> adapters ->
benchmark`. Graph and temporal state are persisted by storage and consumed by
retrieval; neither is allowed to couple the core to Obsidian or an LLM.

## Risks

- Semantic search must remain optional; deterministic lexical retrieval is the
  baseline.
- Imported Markdown and stored memory are untrusted data, never instructions.
- Obsidian sync requires version-aware conflict handling before write-back.
- Consolidation cannot discard provenance or historical truth.

## Testing strategy

Unit-test each lifecycle boundary using temporary SQLite databases. Integration
tests cover remember/search/recall and CLI behavior. Future adapter tests use
temporary vaults, and RMB fixtures remain deterministic with fixed clocks and
inputs.

## Phase 1 acceptance

`remember -> persist -> search -> recall` works offline with typed metadata,
secret blocking, deterministic IDs, explainable scores, and a clean CLI.

## Phase 1 status

Completed: typed memory model, deterministic IDs, privacy filtering, SQLite
and filesystem stores, keyword retrieval, recall guardrails, access tracking,
archive preservation, configuration initialization, and CLI foundation.

Deferred to Phase 2: Obsidian Markdown vault adapter, import/export, and
non-destructive human-edit synchronization.

## Phase 2 status

Completed: safe vault initialization, deterministic Markdown serialization,
stable Redstone IDs, filename sanitization, export/import, archive movement,
hash-based synchronization, privacy-scanned imports, and explicit conflicts.

Phase 3 remains deferred: hybrid ranking, temporal behavior, consolidation,
conflict reasoning, and knowledge graph traversal.

## MVP completion status

Phase 3: deterministic hybrid ranking, bounded context, update versioning,
timeline, supersession, and lightweight related-memory discovery.

Phase 4: local JSON-RPC stdio MCP server exposing compact memory tools.

Phase 5: concise Claude Skill under `skill/redstone-memory`.

Phase 6: deterministic RMB synthetic retrieval benchmark and generated report.

Phase 7: concise release documentation, changelog, and security update.
