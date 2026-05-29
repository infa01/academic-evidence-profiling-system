# ESCO Matching Noise and Mitigation

The ESCO matching pipeline is intentionally treated as an evidence extraction
process, not as a definitive skill assessment. ESCO is a broad occupational
ontology, and semantic matching can produce useful signals as well as noisy or
borderline links.

## Where Noise Can Enter

Noise can appear at two stages:

1. **Learning outcome to ESCO skill matching**
   - Learning outcomes are short and sometimes broad.
   - ESCO skill labels/descriptions may use labour-market language rather than
     curriculum language.
   - Sentence-transformer similarity can retain borderline matches.

2. **ESCO skill to occupation expansion**
   - ESCO occupation relations are intentionally broad.
   - A valid skill match can connect to many occupations.
   - Some occupation links may reflect ontology coverage rather than a meaningful
     student orientation.

## Mitigation Strategy

The system does not hide this uncertainty. Instead, it exposes it.

### Semantic Similarity Threshold

Only ESCO skill candidates above the configured similarity threshold are retained.
The current threshold is defined centrally in:

```text
scripts/methodology_config.py
```

### Match Quality Labels

Retained ESCO skill matches are labelled by semantic quality:

| Label | Meaning |
| --- | --- |
| `strong_semantic_match` | Higher semantic similarity; stronger evidence. |
| `supporting_semantic_match` | Moderate similarity; useful but still contextual. |
| `borderline_semantic_match` | Passed the threshold but should be interpreted cautiously. |

These labels are carried into:

- learning outcome evidence traces;
- raw skill occurrences;
- aggregated skill profiles;
- occupation-orientation summaries;
- final structured JSON;
- dashboard and PDF reporting.

### Occupation Signal Categorisation

Occupation outputs are separated into categories:

| Category | Meaning |
| --- | --- |
| `primary_signal` | Stronger occupation-orientation signal. |
| `supporting_signal` | More than one supporting skill but weaker than primary signals. |
| `low_context_signal` | Retained for transparency, but limited support. |
| `weak_one_off_signal` | Based on one weak skill relation. |
| `possible_noise` | Low-evidence relation likely caused by ontology breadth. |

The dashboard presents a ranked subset of prioritised occupation signals while
still keeping all occupation relations in the JSON output for auditability.

## What This Does Not Solve

These mitigations reduce overclaiming, but they do not make ESCO matching
perfect. The system can still:

- miss implicit skills in a learning outcome;
- retain semantically plausible but contextually weak matches;
- produce occupation links that look surprising;
- depend on the quality and wording of module learning outcomes.

### Out-of-Distribution and Emerging Skills

The system is taxonomy-bound. It can only align learning outcomes to skills and
occupations represented in the ESCO snapshot used by the project. Rapidly
emerging Computer Science areas such as LLMOps, prompt engineering, AI safety or
new cloud-native practices may not be represented with enough detail. In these
cases, the system may map the learning outcome to broader ESCO skills, miss the
specific emerging skill, or retain a borderline/noisy match.

This is handled through transparency rather than automatic invention of new
skills. Future work could combine ESCO with a supplementary Computer Science
taxonomy, an emerging-skills dictionary or periodic ESCO dataset updates.

For this reason, ESCO outputs are described as:

> ESCO skill evidence signals and occupation-orientation signals

They are not described as:

> verified skills, job recommendations, or employability decisions.

## Thesis-Safe Interpretation

A suitable dissertation phrasing is:

> ESCO matching is used as a transparent semantic alignment mechanism between
> curriculum learning outcomes and labour-market skill terminology. Because both
> semantic similarity and ESCO occupation relations may introduce noise, the
> system exposes similarity scores, match-quality labels, supporting skills and
> weak/noise categories. This allows the prototype to support explainable career
> reflection without presenting ESCO links as definitive professional evidence.
