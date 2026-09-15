# RMB — Redstone Memory Benchmark

Dataset: 220 conversations, 5 projects, 25 entities, 72 questions (22 multi-memory).

This is a deterministic synthetic retrieval workload. Results apply to this dataset and do not establish general AI-memory or model performance.

## Baseline

- Recall: 61.11%
- Precision: 77.78%
- F1: 66.20%
- Context: 13.6 tokens

## Redstone Fixed top_k=1

- Recall: 83.33%
- Precision: 100.00%
- F1: 88.43%
- Context: 14.4 tokens
- Retrieval latency: 1.256 ms/question

## Redstone Adaptive

- Recall: 100.00%
- Precision: 95.83%
- F1: 97.02%
- Single-memory accuracy: 100.00%
- Multi-memory accuracy: 100.00%
- Requirement coverage: 100.00%
- Average memories selected: 1.60
- Redundancy rate: 0.00%
- Context: 24.0 tokens
- Retrieval latency: 1.473 ms/question

Fixed vs baseline absolute recall difference: +22.22%
Fixed vs baseline relative recall improvement: +36.36%
Fixed vs baseline context reduction: -5.70%
Adaptive vs fixed recall difference: +16.67%
Adaptive vs fixed context change: +66.38%

## Category Accuracy

- comparison: 50.00%
- contradiction: 50.00%
- current_state: 100.00%
- decision: 100.00%
- distractor: 100.00%
- historical_state: 100.00%
- long_term: 100.00%
- multi_hop: 33.33%
- multi_memory: 33.33%
- preference: 100.00%
- project: 100.00%
- provenance: 100.00%
- redundancy: 100.00%
- short_term: 100.00%
- supersession: 100.00%
- temporal: 50.00%

## Adaptive Category Accuracy

- comparison: 100.00%
- contradiction: 100.00%
- current_state: 100.00%
- decision: 100.00%
- distractor: 100.00%
- historical_state: 100.00%
- long_term: 100.00%
- multi_hop: 100.00%
- multi_memory: 100.00%
- preference: 100.00%
- project: 100.00%
- provenance: 100.00%
- redundancy: 100.00%
- short_term: 100.00%
- supersession: 100.00%
- temporal: 100.00%

## Failure Categories

- none

## Recall by Distance

- 0-10 conversations: 100.00%
- 11-25 conversations: 87.50%
- 26-50 conversations: 100.00%
- 51-100 conversations: 96.49%
- 101+ conversations: 73.58%
