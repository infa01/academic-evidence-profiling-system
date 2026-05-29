# Bloom Taxonomy Methodology

The project uses Revised Bloom's Taxonomy as a cognitive-depth evidence signal.
It helps the system distinguish whether learning outcomes appear to involve
lower-level recall/understanding, applied work, analysis, evaluation or creation.

Bloom classification is not treated as an absolute truth. It is an interpretable
signal used for scoring, XAI and RAG-grounded report generation.

## Why Bloom Is Used

Learning outcomes do not only describe topics. They also describe the expected
cognitive activity of the student. For example, an outcome asking a student to
"describe" a concept carries different cognitive evidence from an outcome asking
the student to "design", "evaluate" or "implement" a solution.

In this project, Bloom supports:

- cognitive-depth weighting in the academic evidence score;
- explanations of why some learning outcomes contribute stronger evidence;
- richer RAG context for final LLM report generation;
- visual analytics showing cognitive depth across module levels.

## Hybrid Classification Approach

The classifier uses a hybrid approach:

1. **Action verb matching**
   - Learning outcome verbs are matched against a Bloom verb taxonomy.
   - Clear single-level verbs can produce high-reliability classifications.

2. **Semantic disambiguation**
   - Some verbs are ambiguous or context-sensitive.
   - Sentence-transformer similarity compares the full learning outcome against
     Bloom level prototype texts.

3. **Conservative fallback**
   - If evidence is weak, the learning outcome can be marked as `Unclassified`
     instead of forcing a misleading level.

4. **Near-tie ambiguity handling**
   - If the semantic margin between the top two Bloom candidates is below
     `0.03`, the learning outcome is marked as `Mixed/Ambiguous`.
   - The top candidate is still retained as `inferred_cognitive_level`, but the
     exported `cognitive_level` remains conservative for scoring and dashboard
     interpretation.

## Reliability Labels

Each Bloom classification includes a reliability label:

| Label | Meaning |
| --- | --- |
| `rule_based_high_reliability` | A clearer action-verb rule assigned the level. |
| `semantic_context_supported` | Semantic context helped select or adjust the level. |
| `conservative_fallback` | The system retained a cautious classification. |
| `low_confidence_unclassified` | The system avoided overclaiming and did not assign a level. |
| `ambiguous_near_tie` | The top Bloom candidates were too close to justify one definitive level. |

The dashboard and final JSON expose these labels so that Bloom evidence remains
auditable.

## Ambiguity Labels

Each result also includes an ambiguity status:

| Label | Meaning |
| --- | --- |
| `single_level_or_clear_signal` | The evidence points clearly to one level. |
| `ambiguous_resolved` | Multiple levels were possible and the classifier resolved them. |
| `mixed_ambiguous_near_tie` | Multiple semantic candidates were nearly tied, so the output is treated as mixed evidence. |
| `close_semantic_margin` | Semantic candidates were close together. |
| `unclassified_low_confidence` | The evidence was too weak for a confident level. |

## Limitations

Bloom classification from learning outcome text has natural limits:

- one learning outcome may contain multiple cognitive demands;
- action verbs can change meaning depending on context;
- module descriptions may omit practical assessment details;
- semantic similarity can help disambiguation but does not replace expert review;
- near-tie candidates are treated as mixed evidence, but this is still not a
  full clause-level multi-label classifier;
- the resulting level should not be treated as proof that learning depth was
  achieved by the student.

## Thesis-Safe Interpretation

A suitable dissertation phrasing is:

> Bloom classification is used as an explainable cognitive-depth signal inferred
> from learning outcome wording. The system combines action-verb rules with
> semantic disambiguation and exposes confidence, ambiguity, near-tie margin and
> reliability metadata. When Bloom candidates are too close, the learning outcome
> is marked as mixed/ambiguous rather than forced into a single definitive level.
> This allows Bloom evidence to support scoring and RAG generation without
> presenting the classification as a definitive measurement of learning depth.
