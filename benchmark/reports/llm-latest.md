# RMB Phase 12 LLM Memory Evaluation

Dataset: 10 synthetic projects, 400 sessions, 400 authored facts, 120 questions. Dataset version: `phase12-authored-v1`. Run timestamp: `2026-09-13T17:38:54.989950+00:00`.

Provider settings (no credentials): `{'provider': 'deterministic', 'model': 'deterministic-extractive-v1', 'temperature': 0, 'max_output_tokens': None, 'network': False}`.

## Method

Equal-budget: baseline receives most recent history limited to 1000 estimated tokens. Redstone receives adaptive retrieval context from same complete project history, also limited to 1000 estimated tokens. Same provider answers both paths. Expected facts never enter provider input.

Full-history ablation: baseline receives full 50000 token history; Redstone remains retrieval-bounded. This is separate from equal-budget results.

Deterministic layer scores normalized required facts, grounding against supplied context, provenance, temporal questions, and unsupported answers. Blind candidate labels are randomized per question and retained only as mappings. An external LLM judge is optional and not run by offline deterministic mode; no judge result is presented as LLM judgment.

## Equal-Budget Results

| Metric | Baseline | Redstone |
| --- | ---: | ---: |
| Answer accuracy | 8.33% | 83.33% |
| Completeness | 8.33% | 87.50% |
| Factuality | 0.00% | 83.33% |
| Relevance | 8.33% | 83.33% |
| Required-fact coverage | 8.33% | 87.50% |
| Provenance accuracy | 0.00% | 100.00% |
| Temporal accuracy | 0.00% | 100.00% |
| Hallucination rate | 100.00% | 16.67% |
| Context tokens | 992.20 | 97.30 |
| Total tokens | 1012.65 | 166.07 |
| Latency ms | 0.48 | 0.06 |

Context reduction: 90.19%.

## Full-History Ablation

| Metric | Baseline | Redstone |
| --- | ---: | ---: |
| Answer accuracy | 91.67% | 83.33% |
| Completeness | 91.67% | 87.50% |
| Factuality | 83.33% | 83.33% |
| Relevance | 91.67% | 83.33% |
| Required-fact coverage | 91.67% | 87.50% |
| Provenance accuracy | 100.00% | 100.00% |
| Temporal accuracy | 100.00% | 100.00% |
| Hallucination rate | 16.67% | 16.67% |
| Context tokens | 50013.90 | 97.30 |
| Total tokens | 50055.72 | 166.07 |
| Latency ms | 28.66 | 0.12 |

## Repeats

Configured repeated-run summary: `{'baseline': {'answer_accuracy': {'mean': 0.08333333333333333, 'minimum': 0.08333333333333333, 'maximum': 0.08333333333333333, 'stddev': 0.0}, 'completeness': {'mean': 0.08333333333333333, 'minimum': 0.08333333333333333, 'maximum': 0.08333333333333333, 'stddev': 0.0}, 'factuality': {'mean': 0.0, 'minimum': 0.0, 'maximum': 0.0, 'stddev': 0.0}, 'context_tokens': {'mean': 992.2, 'minimum': 992.2, 'maximum': 992.2, 'stddev': 0.0}, 'total_tokens': {'mean': 1012.65, 'minimum': 1012.65, 'maximum': 1012.65, 'stddev': 0.0}, 'latency_ms': {'mean': 0.4844124994027273, 'minimum': 0.4844124994027273, 'maximum': 0.4844124994027273, 'stddev': 0.0}}, 'redstone': {'answer_accuracy': {'mean': 0.8333333333333334, 'minimum': 0.8333333333333334, 'maximum': 0.8333333333333334, 'stddev': 0.0}, 'completeness': {'mean': 0.875, 'minimum': 0.875, 'maximum': 0.875, 'stddev': 0.0}, 'factuality': {'mean': 0.8333333333333334, 'minimum': 0.8333333333333334, 'maximum': 0.8333333333333334, 'stddev': 0.0}, 'context_tokens': {'mean': 97.3, 'minimum': 97.3, 'maximum': 97.3, 'stddev': 0.0}, 'total_tokens': {'mean': 166.075, 'minimum': 166.075, 'maximum': 166.075, 'stddev': 0.0}, 'latency_ms': {'mean': 0.06251166657117817, 'minimum': 0.06251166657117817, 'maximum': 0.06251166657117817, 'stddev': 0.0}}}`. Deterministic provider has no sampling variance; real providers should use `--runs 3` on a declared subset before interpreting variance. No statistical-significance claim is made.

## Limitations

Synthetic authored data; estimated token counts; deterministic scorer cannot assess arbitrary prose quality. A real provider run requires explicit environment credentials and may have provider cost, latency, context-window, and version changes. No embeddings, vector database, reranker, cloud memory, or memory consolidation is used.
