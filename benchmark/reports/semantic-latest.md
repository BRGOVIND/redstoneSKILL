# RMB Phase 13 Semantic Retrieval A/B

Dataset: 50 targeted semantic/paraphrase questions derived from Phase 12's 10-project, 400-session history. Provider: deterministic local hash embedding test model. No API calls. Semantic candidates feed existing adaptive selection; lexical temporal filters remain active.

| Strategy | Recall | F1 | Answer accuracy | Context tokens | Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 64.00% | 64.00% | 64.00% | 92.1 | 0.871 |
| semantic | 46.00% | 46.00% | 46.00% | 83.5 | 0.330 |
| hybrid | 64.00% | 64.00% | 64.00% | 91.4 | 1.545 |

## Does Redstone Need Semantic Retrieval?

NO

Evidence: semantic recall and answer accuracy are lower than lexical control on complete 50-question targeted subset. This local deterministic embedding is an investigation harness, not evidence that a production cloud embedding model will improve real LLM results. Do not enable semantic retrieval by default; preserve lexical temporal ranking.
