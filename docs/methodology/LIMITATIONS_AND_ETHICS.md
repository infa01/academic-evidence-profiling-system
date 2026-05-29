# Limitations and Ethics

This project is an explainable academic evidence profiling prototype. It should
be interpreted as decision support for reflection, not as an automated assessment
or career decision system.

## Core Limitation

The system does not measure professional competence. It constructs academic
evidence signals from module learning outcomes, student grades, Bloom taxonomy,
ESCO semantic matching and RAG-grounded generation.

The appropriate interpretation is:

> explainable academic evidence for career reflection

The inappropriate interpretation is:

> proof of professional ability or job suitability

## Scoring Limitations

The scoring method is theoretical and heuristic.

Limitations:

- the score is not externally validated as a measure of competence;
- weights and thresholds affect ranking;
- grades are academic performance signals, not direct skill measurements;
- module level is only an approximate academic-depth signal;
- scores are best compared within the same student profile, not across students.

Mitigations:

- formula and weights are exposed in the dashboard, JSON and PDF;
- scoring is described as academic evidence strength;
- methodology notes and limitations are included in generated outputs.

## Bloom Taxonomy Limitations

Bloom classification is inferred from learning outcome wording.

Limitations:

- one learning outcome may contain multiple cognitive demands;
- action verbs can be ambiguous or context-sensitive;
- semantic disambiguation can help but cannot replace expert review;
- Bloom level does not prove achieved learning depth.

Mitigations:

- confidence, ambiguity and reliability metadata are stored;
- low-confidence results can be marked as `Unclassified`;
- Bloom is treated as cognitive-depth evidence, not definitive classification.

## ESCO Matching Limitations

ESCO is a broad labour-market ontology. Semantic matching and occupation
expansion may introduce noise.

Limitations:

- semantic similarity may retain borderline skill matches;
- implicit skills may be missed;
- ESCO skill-to-occupation relations can expand into many occupations;
- some occupation signals may reflect ontology breadth rather than meaningful
  career direction.

Mitigations:

- similarity scores and match-quality labels are exposed;
- weak/noise occupation categories are retained separately;
- occupation outputs are described as orientation signals, not recommendations;
- supporting skills are shown for prioritised occupation signals.

## RAG and LLM Limitations

RAG constrains generation but does not guarantee perfect output.

Limitations:

- an LLM can still overgeneralise or phrase evidence too strongly;
- retrieval quality affects generation quality;
- deterministic quality checks cannot prove factual correctness;
- generated reports require human review.

Mitigations:

- retrieved evidence is stored and displayed;
- prompts include strict evidence boundaries;
- prompt transparency files are exported;
- generation metadata records retrieval summary and quality checks;
- forbidden overclaiming phrases are checked after generation.

## Privacy and Data Protection

The prototype uses student academic input such as selected modules and grades.
These should be treated as sensitive educational data.

Recommended safeguards:

- keep data local during prototype use;
- avoid storing unnecessary personal identifiers;
- anonymise student examples where possible;
- do not upload student data to third-party LLM services without consent;
- make the generated profile accessible to the student/user.

The current prototype is designed around local file-based execution and optional
local Ollama generation, which helps reduce third-party data exposure.

## Human Oversight

Human review is required before using outputs for academic, employability or
career decisions.

The system should support:

- student reflection;
- advisor discussion;
- CV drafting;
- portfolio planning;
- dissertation demonstration.

It should not be used for:

- automated hiring;
- automated academic assessment;
- ranking students against one another;
- excluding students from opportunities.

## Fairness and Bias

Potential bias can enter through:

- ESCO ontology structure;
- wording of learning outcomes;
- grade distributions;
- model embeddings;
- LLM generation style;
- unequal student access to evidence-rich modules or projects.

Mitigations:

- keep outputs explainable and auditable;
- avoid definitive labels such as "fit", "best", "expert" or "qualified";
- retain limitations in the dashboard and PDF;
- frame occupation outputs as possible directions for exploration;
- require human judgement.

## EU AI Act and Risk Framing

The prototype touches educational and career guidance contexts, so it should be
framed cautiously. It should not be presented as an automated decision-making
system.

The responsible framing is:

> a human-reviewed educational analytics prototype that supports explainable
> career reflection

The unsafe framing is:

> an AI system that decides student employability or recommends jobs

## Thesis-Safe Interpretation

A suitable dissertation phrasing is:

> The prototype is designed as an explainable, human-reviewed academic evidence
> profiling system. It uses structured evidence, transparent scoring, taxonomy
> mappings and controlled RAG generation to support career reflection. Its
> outputs are intentionally framed as indicative and interpretive, not as
> validated professional assessments or automated career decisions.
