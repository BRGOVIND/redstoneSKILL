# RMB Phase 14 Memory Lifecycle

Dataset: 20 projects, 1100 events/candidates, 500 questions. Categories: constraint, decision, episodic, goal, preference, procedural, project, relationship, semantic.

## Memory Growth

| Events | Stored | Active | Superseded | Archived | Duplicates |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 40 | 33 | 6 | 1 | 8 |
| 250 | 103 | 84 | 15 | 4 | 20 |
| 500 | 194 | 158 | 27 | 9 | 36 |
| 1000 | 388 | 316 | 54 | 18 | 72 |
| 1100 | 420 | 340 | 60 | 20 | 80 |

## Retrieval Stability

| Memory Store Size | Recall | Precision | F1 | Context Tokens | Latency ms |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 40 | 100.00% | 100.00% | 100.00% | 142.2 | 1.305 |
| 103 | 100.00% | 100.00% | 100.00% | 142.2 | 1.398 |
| 194 | 100.00% | 100.00% | 100.00% | 142.2 | 1.461 |
| 388 | 98.90% | 98.90% | 98.90% | 141.0 | 2.259 |
| 420 | 100.00% | 100.00% | 100.00% | 142.2 | 2.574 |

## Lifecycle Quality

- Formation precision: 100.00%
- Duplicate rate: 7.27%
- Stale current-state rate: 0.00%
- Historical linked-memory retention: 14.29%
- Unresolved contradiction pairs: 20
- Privacy candidates blocked: 60
- Provenance preserved: True
- Restart integrity: True
- Obsidian round-trip integrity: True

## Consolidation

Only exact deterministic duplicates collapsed. Near-duplicates, contradictions, and superseded historical states remain physically stored. Before: 1100 candidates. After: 420 memories. Collapsed: 80. Historical memories preserved: 60.

## Limitations

Deterministic authored synthetic workload. No LLM consolidation. No Phase 14 embeddings. Near-duplicates remain because safe equivalence is not established. Genuine contradictions remain unresolved when evidence is ambiguous. Results do not establish universal memory quality.
