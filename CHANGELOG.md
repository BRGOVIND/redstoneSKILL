# Changelog

## 0.1.0

Initial public release of Redstone's local-first memory engine.

### Included

- Local typed memory, SQLite, filesystem and Obsidian adapters.
- Deterministic hybrid ranking, temporal supersession, relations, and context.
- Local stdio MCP tools, Claude skill, and RMB benchmark.
- Hard RMB dataset with 220 conversations, retrieval curves, failure analysis,
  intent-aware temporal ranking, stopword filtering, and targeted synonyms.
- Coverage-aware multi-memory retrieval, redundancy suppression, bounded
  relationship expansion, temporal context composition, and recall diagnostics.
- RMB expanded to 72 questions with 22 multi-memory cases and adaptive metrics.
- Answer-level RMB with 10 authored long-running projects, 100 sessions, 110
  grounded questions, provider-neutral generation, equal-budget comparison, and
  retrieval/context/answer failure attribution.
- Phase 11 robustness RMB with 160 adversarial sessions, 150 stored memories,
  130 questions, abstention and safety scoring, strict/semantic provenance,
  similar-entity ranking, date-aware retrieval, and contradiction requirements.
- Phase 12 provider-neutral LLM evaluation with offline deterministic mode,
  optional OpenAI adapter, credential-safe configuration, equal-budget and
  full-history ablations, 1K-50K context curves, blind candidate labels,
  repeat summaries, and 120-question synthetic long-running histories.
- Phase 13 optional semantic candidate investigation with deterministic local
  embeddings, SQLite cache, OpenAI embedding adapter, lexical/semantic/hybrid
  A/B evaluation, targeted paraphrase subset, and temporal-preserving controls.
- Phase 14 deterministic candidate formation and long-horizon lifecycle RMB
  covering 1,100 events, safe duplicate collapse, supersession, pollution,
  privacy, persistence, retrieval stability, and Obsidian round trips.
- Phase 15 deterministic temporal/conflict composer with complete revision-chain
  expansion, date-effective state, uncertainty, context isolation, structured
  provenance, and a 500-scenario benchmark.
- Phase 16 production integration with idempotent initialization, non-mutating
  diagnostics, isolated smoke testing, reusable MCP dispatch, deterministic
  wheel-carried Claude Skill packaging, and validated Obsidian round trips.
- Phase 17 live-client validation workflow, MCP supersession support, packaged
  Claude Code Skill instructions, isolated cross-process evidence, and explicit
  reporting when Claude usage limits block live model scenarios.

### Known limitations

- Lexical retrieval is the default. Semantic retrieval was evaluated but not adopted.
- No LLM memory consolidation or cloud memory backend.
- No web or mobile interface.
- Live Claude model validation is `NOT RUN`; external client/API attempts failed before inference.
- Benchmarks are synthetic or authored and are not universal real-world performance claims.
