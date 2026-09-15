# RMB Phase 15 Temporal and Conflict Composition

Root cause: Phase 14 adaptive selection stopped timelines after two memories once abstract requirements were covered, and duplicate suppression rejected the second unresolved-conflict candidate. Phase 15 keeps complete bounded chains and contradiction candidates, then composes structured state with provenance.

Dataset: 20 projects, 280 memories, 500 authored scenarios/questions.

| Metric | Phase 14 | Phase 15 |
| --- | ---: | ---: |
| Timeline/conflict accuracy | 50.00% | 100.00% |
| Current-state accuracy | not measured | 100.00% |
| Historical-state accuracy | not measured | 100.00% |
| Conflict accuracy | not measured | 100.00% |
| Decision-history accuracy | not measured | 100.00% |
| Retrieval recall | 80.00% | 40.13% |
| Retrieval precision | 90.00% | 55.20% |
| Retrieval F1 | 83.33% | 41.40% |
| Context sufficiency | not measured | 100.00% |
| Provenance | 100.00% | 100.00% |
| Context tokens | 116.7 | 586.2 |
| End-to-end latency | not comparable | 6.583 ms |

## Categories

- context: 100.00%
- current: 100.00%
- date: 100.00%
- decision: 100.00%
- five_state: 100.00%
- historical: 100.00%
- mixed: 100.00%
- partial: 100.00%
- provenance: 100.00%
- resolved: 100.00%
- three_state: 100.00%
- timeline: 100.00%
- unresolved: 100.00%

## Limitations

Deterministic authored workload and reasoning. No LLM composition, embeddings, or universal temporal-reasoning claim. Month-only date queries assume one calendar year. Unlinked ambiguous memories remain uncertain. Content subject extraction is conservative and cannot resolve every natural-language relation.
