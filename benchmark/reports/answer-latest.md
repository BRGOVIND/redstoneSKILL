# RMB Answer-Level Benchmark

Dataset: 10 projects, 100 sessions, 110 questions.

Provider: `DeterministicAnswerProvider`. This deterministic extractive provider tests the pipeline without external APIs; it does not measure general LLM quality.

Both paths receive at most 180 context tokens. Baseline receives the most recent project history fitting that budget. Redstone receives adaptive context retrieved from the same history.

## Baseline

- Answer accuracy: 65.45%
- Completeness: 65.91%
- Factuality: 66.36%
- Required-fact coverage: 65.91%
- Provenance accuracy: 0.00%
- Context pass rate: 91.82%
- Context: 162.8 tokens
- Pipeline latency: 0.165 ms/question

## Redstone

- Answer accuracy: 100.00%
- Completeness: 100.00%
- Factuality: 100.00%
- Required-fact coverage: 100.00%
- Provenance accuracy: 100.00%
- Retrieval recall: 98.18%
- Retrieval precision: 94.09%
- Retrieval F1: 95.45%
- Requirement coverage: 100.00%
- Context pass rate: 100.00%
- Context: 120.8 tokens
- Pipeline latency: 1.744 ms/question

Answer accuracy difference: +34.55%
Context reduction: 25.82%

Stage attributions:
- Baseline: retrieval_failure=49, answer_generation_failure=29
- Redstone: retrieval_failure=2

## Category Accuracy

- comparison: baseline 100.00%; Redstone 100.00%
- constraint: baseline 10.00%; Redstone 100.00%
- current_state: baseline 100.00%; Redstone 100.00%
- decision: baseline 100.00%; Redstone 100.00%
- distractor: baseline 100.00%; Redstone 100.00%
- historical_state: baseline 100.00%; Redstone 100.00%
- multi_memory: baseline 100.00%; Redstone 100.00%
- preference: baseline 0.00%; Redstone 100.00%
- project: baseline 10.00%; Redstone 100.00%
- provenance: baseline 0.00%; Redstone 100.00%
- timeline: baseline 100.00%; Redstone 100.00%

## Interpretation

RMB is synthetic. Results measure deterministic extractive answer generation over authored workloads, not open-ended LLM reasoning or general AI-memory quality.
