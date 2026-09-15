# RMB: Redstone Memory Benchmark

Benchmark commands run from a Redstone source checkout. The runtime wheel omits
benchmark assets; they remain in the repository and source distribution for
reproducibility.

RMB measures deterministic retrieval over 220 noisy conversations spanning five
projects and 25 entities. Dataset includes 30+ decisions, 20 preferences,
supersession, contradictions, duplicates, cross-project distractors, provenance,
multi-hop relationships, and long-range questions. Its 72 questions include 22
that require multiple complementary memories.

Baseline performs raw lexical retrieval over conversation text. Redstone uses
same conversations plus structured project, temporal, relationship, importance,
and provenance metadata. Fixed retrieval uses the same `top_k`; adaptive
retrieval greedily stops after covering deterministic information requirements
or exhausting its memory/token budget. No LLM or embedding service participates.

```bash
redstone benchmark
```

Fixed seed `8128` makes dataset and quality metrics reproducible. Runtime latency
naturally varies. Reports cover fixed `top_k` 1, 2, 3, 5, and 10 plus adaptive
retrieval. Current measured results live in `benchmark/reports/latest.md`;
adaptive failures live in `benchmark/reports/failure-analysis.md`.

On the synthetic Phase 9 RMB workload, the measured top-1 comparison is baseline recall 61.11% and F1 66.20%; fixed
Redstone recall 83.33% and F1 88.43%; adaptive Redstone recall/F1 100.00%.
Adaptive improves recall by 16.67 percentage points over fixed top-1, reaches
100.00% multi-memory accuracy, selects 1.60 memories on average, and uses 24.0
tokens versus fixed top-1's 14.4. Dataset remains synthetic and evaluates
retrieval, not generated-answer quality.

## Answer-Level RMB

Phase 10 separates retrieval, context sufficiency, and final-answer quality. Its
authored public-style dataset contains 10 projects, 10 sessions per project, and
110 questions covering current and historical state, decisions, timelines,
preferences, comparisons, constraints, provenance, distractors, and multi-memory
answers. No private user data is used.

Both paths use the same 180-token limit. Baseline receives the most recent
conversation history for the project named in the question; cross-project
questions receive recent global history. Redstone ingests the same history and
supplies adaptive context. Neither path receives expected facts or answers.

`AnswerProvider` keeps generation provider-independent. Current reproducible run
uses `DeterministicAnswerProvider`, an extractive test provider with no network
or model dependency. Evaluation supports normalized answers, required-fact
coverage, provenance, factual grounding, and stage-specific failure attribution.
See `benchmark/reports/answer-latest.md` for measured results. These results test
the pipeline, not general LLM quality.

Current authored-v1 run measures 65.45% baseline answer accuracy and 100.00%
Redstone answer accuracy, with 25.82% less context. Redstone retrieval recall is
98.18%, while context sufficiency and answer accuracy are 100.00%; two exact-ID
misses were covered by equivalent grounded evidence. Factuality checks required
ground-truth facts against supplied context and does not detect arbitrary facts
outside the authored specification.

## Robustness RMB

Run `redstone benchmark robustness` to evaluate adversarial memory conditions.
The deterministic `robustness-authored-v1` dataset contains 10 projects, 160
sessions, 150 stored memories, and 130 questions. Each category has 10 cases,
with 20 historical-state cases. Exact duplicates intentionally collapse during
ingestion.

Categories cover current and historical state, three-state timelines,
contradictions, similar entities, lexical distractors, duplicates and
near-duplicates, partial evidence, unsupported questions, provenance,
multi-memory temporal questions, and instruction-like memory content. The
benchmark records retrieval, context, answer, uncertainty, provenance, temporal,
entity, stale-memory, hallucination, security, redundancy, context, and latency
metrics independently.

Both paths use `DeterministicAnswerProvider` and a 220-token budget. Baseline
receives recent project history. Redstone retrieves at most five memories with
relationship depth one from the same history. Expected facts never enter either
provider input.

Current measured results: baseline answer accuracy 62.31%, Redstone answer
accuracy 100.00%, Redstone retrieval F1 82.05%, context reduction 41.46%, and
zero unsupported-answer, hallucination, stale-memory, or adversarial instruction
execution errors. Exact answer accuracy is 7.69% because extractive answers
retain evidence and provenance around required facts; required-fact accuracy is
100.00%. Results are synthetic and do not evaluate open-ended LLM behavior.

## Phase 12 LLM Evaluation

`redstone benchmark llm` evaluates 120 questions over 10 synthetic projects,
400 sessions, and 400 authored facts. The primary equal-budget condition gives
both paths at most 1,000 estimated input tokens: baseline gets latest history;
Redstone gets adaptive context retrieved from same complete history. A separate
full-history ablation gives baseline full history and never mixes those metrics
with equal-budget results. Long-context curves cover 1K, 5K, 10K, 25K, and 50K
history lengths; curve runs use first 20 declared questions for cost control.

Default provider is deterministic/offline. Real OpenAI mode requires
`OPENAI_API_KEY` and `REDSTONE_LLM_MODEL`, for example:

```bash
redstone benchmark llm --provider openai --runs 3 --max-questions 20
```

Provider metadata, temperature 0, output limit, dataset version, token counts,
latency, blind candidate labels, and failure attribution are recorded without
credentials. Deterministic scoring checks required facts, grounding,
provenance, temporal answers, and unsupported answers. An external blind LLM
judge is not claimed by offline runs. Reports are synthetic and not statistical
evidence of general LLM-memory performance.

The deterministic Phase 12 run measures 8.33% equal-budget baseline accuracy,
83.33% equal-budget Redstone accuracy, and 91.67% full-history baseline accuracy.
Its result is context efficiency under the equal-budget condition; it does not
show Redstone outperforming full history.

## Phase 13 Semantic Investigation

`redstone benchmark semantic` preserves lexical retrieval as control and tests
semantic candidates plus hybrid candidates on 50 Phase 12-derived paraphrase
questions. Default deterministic embeddings are local, reproducible, and cached
by memory content hash/provider/model in SQLite. Optional OpenAI embeddings
require `OPENAI_API_KEY` and `REDSTONE_EMBEDDING_MODEL`; no key is persisted.
Semantic candidates still pass temporal filters and existing adaptive selection.
See `phase12-gap-analysis.md` before interpreting the A/B results.

## Phase 14 Lifecycle Stability

`redstone benchmark lifecycle` processes 1,100 deterministic candidates across
20 projects and evaluates 500 current, historical, timeline, duplicate, and
conflict questions. Checkpoints at 100, 250, 500, 1,000, and 1,100 events record
store growth, duplicate/privacy/noise rejection, retrieval quality, context
size, and latency. Restart equality and SQLite-to-Obsidian-to-SQLite counts are
verified.

Formation rejects only empty or obvious acknowledgement noise. Existing privacy
policy remains authoritative. Exact content/type/project duplicates collapse by
deterministic ID. Near-duplicates, ambiguous contradictions, and superseded
history remain stored because deterministic merging cannot prove equivalence.
No LLM consolidation or Phase 14 embeddings participate.

## Phase 15 Temporal and Conflict Composition

`redstone benchmark temporal` evaluates 500 authored scenarios over 20 projects
and revision chains up to 10 states. Retrieval remains lexical. A deterministic
composer expands explicit supersession links, orders evidence by observation
time, derives current and month-effective state, distinguishes resolved from
unresolved conflicts, isolates entity-specific contexts, and preserves memory
IDs, source sessions, and timestamps in output context.

Phase 14's 50% timeline/conflict limitation came from early adaptive stopping
and conflict candidates being rejected as redundant. Phase 15 keeps bounded
timeline and contradiction candidates without changing single-memory defaults.
Ambiguous unlinked claims remain uncertain. No embeddings or LLM composition
participate.

## Reproducibility

All default commands are deterministic and require no model credentials:

| Workload | Command | Primary outputs |
| --- | --- | --- |
| Phase 9 retrieval + Phase 10 answers | `redstone benchmark core` | `latest.*`, `answer-latest.*` |
| Phase 11 robustness | `redstone benchmark robustness` | `robustness-latest.*` |
| Phase 12 long context | `redstone benchmark llm --provider deterministic` | `llm-latest.*`, `llm-long-context.md` |
| Phase 13 semantic investigation | `redstone benchmark semantic` | `semantic-latest.*` |
| Phase 14 lifecycle | `redstone benchmark lifecycle` | `lifecycle-latest.*` |
| Phase 15 temporal composition | `redstone benchmark temporal` | `temporal-latest.*` |

JSON files under `benchmark/results/` contain per-question records,
configuration, population sizes, and aggregate metrics. Markdown under
`benchmark/reports/` provides interpretation and failure attribution. Dataset
generators are the corresponding `*_dataset.py` modules; fixed seeds and
authored IDs make quality results reproducible, while wall-clock latency varies
by machine. Baselines, context budgets, and providers are defined in each phase
section above. None of these workloads uses private user conversations or proves
general real-world model performance.
