# Scoring Methodology

This project uses scoring as an explainable academic evidence-ranking mechanism.
The score is not intended to measure professional competence, certify skill
mastery, or make automated career decisions. Its purpose is to prioritise and
explain evidence extracted from learning outcomes, student grades, Bloom levels
and ESCO semantic matches.

## Scoring Purpose

The scoring system supports three prototype needs:

- ranking ESCO-aligned skill evidence within a student profile;
- explaining why a skill or occupation-orientation signal appears in the dashboard;
- selecting structured evidence chunks for RAG-grounded LLM generation.

The score should therefore be read as:

> academic evidence strength within the current profile

It should not be read as:

> professional proficiency, employability probability, or job suitability.

## Occurrence-Level Formula

Each ESCO skill occurrence is produced from a single learning outcome and a
matched ESCO skill. Its evidence score is calculated as:

```text
occurrence_evidence_score =
    grade_weight
    x semantic_similarity_score
    x bloom_weight
    x module_level_weight
```

The components are:

| Component | Meaning |
| --- | --- |
| `grade_weight` | Normalized academic performance signal for the module. |
| `semantic_similarity_score` | Sentence-transformer cosine similarity between learning outcome text and ESCO skill evidence. |
| `bloom_weight` | Cognitive-depth weight from the classified Revised Bloom level. |
| `module_level_weight` | Approximate academic-depth signal derived from the module level. |

## Module Level Weighting

Module levels are treated as approximate academic depth signals:

| Module Level | Interpretation | Weight |
| --- | --- | --- |
| Level 4 | Foundational first-year evidence | `0.90` |
| Level 5 | Intermediate second-year evidence | `1.00` |
| Level 6 | Advanced final-year evidence | `1.10` |

This weighting is intentionally conservative. It reflects the assumption that
later modules usually carry deeper academic evidence, but it does not claim that
module level alone proves stronger professional ability.

## Bloom Weighting

Bloom levels provide a cognitive-depth signal. Higher Bloom levels receive higher
weights, but the maximum is capped to avoid overstating the effect of cognitive
classification.

| Bloom Level | Weight |
| --- | --- |
| Remember | `0.55` |
| Understand | `0.63` |
| Apply | `0.72` |
| Analyse / Analyze | `0.78` |
| Evaluate | `0.82` |
| Create | `0.85` |
| Mixed/Ambiguous | `0.63` |
| Unclassified / Unknown | `0.63` |

Bloom classification is approximate because learning outcomes can contain
multiple cognitive demands and action verbs can change meaning depending on
context. When the top two semantic Bloom candidates have a margin below `0.03`,
the output is marked as `Mixed/Ambiguous` and receives a conservative weight
instead of inheriting a high-level Bloom boost from an unstable near-tie.

## Aggregation

The same ESCO skill may appear across multiple learning outcomes or modules.
The system groups occurrences by ESCO skill URI and calculates an aggregated
academic evidence score from the occurrence-level scores.

The aggregated score is used for ranked skill evidence, semantic domain
strength, occupation-orientation scoring and RAG retrieval priority.

## Academic Evidence Ceiling

Scores are normalized against a theoretical academic evidence ceiling:

```text
1.00 grade weight
x 1.00 semantic similarity max
x 0.85 Bloom max
x 1.10 Level 6 module weight
= 0.935
```

This ceiling is not a universal benchmark. It is a transparent upper bound for
the current scoring model so that user-facing percentages remain conservative.

## Interpretation Labels

Academic normalized scores are mapped to evidence labels:

| Normalized Score | Label |
| --- | --- |
| `>= 0.80` | Very Strong Evidence |
| `>= 0.65` | Strong Evidence |
| `>= 0.50` | Moderate Evidence |
| `>= 0.35` | Emerging Evidence |
| `< 0.35` | Limited Evidence |

These labels describe the strength of academic evidence in the extracted profile.
They do not describe professional mastery.

## Sensitivity and Limitations

The score is sensitive to methodology choices:

- changing the ESCO similarity threshold may add or remove matched skills;
- changing Bloom weights may shift cognitive-depth emphasis;
- changing module-level weights may change the importance of later modules;
- grade distributions affect which modules dominate the evidence profile;
- learning outcome wording affects both Bloom classification and ESCO matching.

For this reason, the dashboard, final JSON and PDF expose scoring components,
formulas, weights and methodology notes. The system prioritises explainability
over claiming objective measurement.

## Thesis-Safe Interpretation

A suitable dissertation phrasing is:

> The scoring methodology provides a transparent academic evidence-strength
> heuristic for ranking and explaining ESCO-aligned skill signals. It combines
> student performance evidence, semantic similarity, Bloom cognitive depth and
> module level weighting. The resulting score supports XAI interpretation and
> RAG retrieval, but should not be interpreted as a validated measurement of
> professional competence.
