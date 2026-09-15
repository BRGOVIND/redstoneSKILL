# Phase 12 Gap Analysis

Analysis completed before semantic retrieval implementation.

Full-history correct / lexical Redstone incorrect: 10 questions.

| Question | Category | Earliest stage | Cause |
| --- | --- | --- | --- |
| atlas-decision | decision | retrieval_failure | synonym/paraphrase |
| beacon-decision | decision | retrieval_failure | synonym/paraphrase |
| cedar-decision | decision | retrieval_failure | synonym/paraphrase |
| delta-decision | decision | retrieval_failure | synonym/paraphrase |
| ember-decision | decision | retrieval_failure | synonym/paraphrase |
| forge-decision | decision | retrieval_failure | synonym/paraphrase |
| grove-decision | decision | retrieval_failure | synonym/paraphrase |
| harbor-decision | decision | retrieval_failure | synonym/paraphrase |
| ion-decision | decision | retrieval_failure | synonym/paraphrase |
| juniper-decision | decision | retrieval_failure | synonym/paraphrase |

## Finding

All gap cases are decision questions. Lexical retrieval selected current-state evidence but omitted migration rationale required by paraphrased `selected`/`why` wording. This is a retrieval/ranking candidate-coverage limitation, not context truncation. Preference failures occur in both paths and are deterministic answer-generation limits, so they are excluded from this gap. Semantic candidate retrieval is justified for controlled A/B testing only; temporal ranking remains control.
