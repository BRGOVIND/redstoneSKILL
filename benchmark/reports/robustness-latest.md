# RMB Robustness Benchmark

Dataset: 10 projects, 160 sessions, 150 stored memories, 130 questions.

Version: `robustness-authored-v1`. Provider: `DeterministicAnswerProvider`. Context budget: 220 tokens. Maximum memories: 5.

Both paths use identical questions, answer provider, token budget, and scoring. Baseline receives recent history. Redstone receives adaptive context from the same authored history.

| Metric | Baseline | Redstone |
| --- | ---: | ---: |
| Answer accuracy | 62.31% | 100.00% |
| Completeness | 77.69% | 100.00% |
| Factuality | 76.92% | 100.00% |
| Retrieval recall | 41.03% | 84.62% |
| Retrieval precision | 7.69% | 77.69% |
| Retrieval F1 | 12.65% | 80.13% |
| Context sufficiency | 85.38% | 100.00% |
| Context reduction | 0.00% | 41.08% |
| Provenance accuracy | 0.00% | 100.00% |
| Temporal accuracy | 60.00% | 100.00% |
| Contradiction accuracy | 100.00% | 100.00% |
| Entity accuracy | 0.00% | 100.00% |
| Unsupported-answer rate | 0.00% | 0.00% |
| Adversarial failure rate | 0.00% | 0.00% |
| Latency | 0.181 ms | 1.475 ms |

Additional Redstone metrics: exact accuracy 7.69%; normalized accuracy 7.69%; required-fact accuracy 100.00%; requirement coverage 100.00%; false-positive rate 22.31%; redundant retrieval 0.00%; average selected memories 1.54; context 124.5 tokens; hallucination 0.00%; stale-memory errors 0.00%.

## Categories

- adversarial: 10
- contradiction: 10
- current_state: 10
- distractor: 10
- duplicate: 10
- entity: 10
- historical_state: 20
- incomplete: 10
- provenance: 10
- temporal_multi: 10
- timeline: 10
- unsupported: 10

## Failure Attribution

- retrieval_failure: 0
- context_failure: 0
- generation_failure: 0
- evaluation_failure: 0
- uncertainty_failure: 0
- temporal_failure: 0
- provenance_failure: 0
- security_failure: 0

Memory mutations during answer generation: 0.

## Interpretation

This deterministic authored benchmark uses synthetic adversarial cases and an extractive provider. It does not evaluate open-ended LLM behavior or prove general memory-system superiority. Factuality is limited to authored ground truth.
