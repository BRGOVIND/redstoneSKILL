# Retrieval Evaluation

Phase 8 exposed failures on paraphrased storage and UI questions, historical
state, current-state provenance, and strict top-1 composition. Retrieval now
detects current, historical, timeline, comparison, provenance, and multi-memory
intent and represents deterministic information requirements.

Ranking remains deterministic and explainable. Adaptive retrieval builds a
bounded candidate pool, performs limited relationship expansion, and greedily
maximizes requirement coverage plus rank score while penalizing redundant
evidence. It stops on coverage, `max_memories`, or `max_tokens`.

The context composer emits only relevant current, historical, and related
sections. Every item retains memory ID, source, confidence, retrieval score, and
reason; recalled memory is explicitly marked as untrusted data. Fixed `search`
behavior remains available, while `recall` and MCP `memory_recall` use adaptive
selection. Retrieval curves expose the context/quality tradeoff.

Answer-level evaluation consumes this retrieval layer without changing runtime
memory APIs. A small `AnswerProvider` protocol accepts only question and context.
The evaluator records retrieval correctness, context sufficiency, and answer
correctness independently, then attributes failures to retrieval, context
construction, or answer generation. Expected answers remain evaluator-only data.
