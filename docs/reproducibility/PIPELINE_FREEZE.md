# Pipeline Freeze

This document defines the current canonical project pipeline. It is the baseline
for cleanup, README rewriting, architecture diagrams and dissertation writing.

## Canonical Pipeline

```text
Student Input
→ Module Learning Outcomes
→ Bloom Cognitive-Depth Evidence
→ ESCO Skill Extraction
→ Semantic Similarity Filtering + Match Quality
→ Student Performance Evidence
→ Academic Evidence Scoring
→ Aggregated ESCO Skill Profile
→ ESCO Concept Interpretation
→ Semantic Skill Domains
→ ESCO Occupation-Orientation Signals
→ Final Structured Evidence Profile JSON
→ Visual Analytics
→ Controlled RAG Retrieval
→ Generic / Targeted LLM Generation
→ Dashboard + PDF Export
```

## Core Evidence Scripts

These scripts form the deterministic evidence pipeline:

| Order | Script | Purpose |
| --- | --- | --- |
| 1 | `scripts/bloom_mapper.py` | Adds Bloom cognitive-depth evidence to module learning outcomes. |
| 2 | `scripts/esco_extractor.py` | Extracts candidate ESCO skills from Bloom-enriched learning outcomes. |
| 3 | `scripts/semantic_similarity.py` | Filters ESCO skills by sentence-transformer similarity and labels match quality. |
| 4 | `scripts/student_profile.py` | Combines selected modules, grades, Bloom evidence and ESCO matches into raw student skill occurrences. |
| 5 | `scripts/aggregate_profile.py` | Aggregates repeated ESCO skill evidence and stores XAI scoring components. |
| 6 | `scripts/enrich_aggregated_profile.py` | Adds ESCO preferred labels and metadata to aggregated skills. |
| 7 | `scripts/calibrate_scores.py` | Normalizes academic evidence scores and adds calibration metadata. |
| 8 | `scripts/interpret_esco_concepts.py` | Adds ESCO concept interpretation, skill type, reuse level and occupation links. |
| 9 | `scripts/cluster_skills.py` | Creates semantic skill domains from ESCO-aligned skill evidence. |
| 10 | `scripts/derive_occupation_orientation.py` | Derives ESCO occupation-orientation signals and weak/noise categories. |
| 11 | `scripts/build_final_profile.py` | Builds the canonical final structured evidence profile JSON. |

## Visual Analytics Scripts

These scripts generate dashboard/PDF chart artifacts:

| Script | Purpose |
| --- | --- |
| `scripts/visualise_top_skills.py` | Ranked ESCO skill evidence chart. |
| `scripts/visualise_bloom_distribution.py` | Bloom cognitive depth by module level. |
| `scripts/visualise_domain_strength.py` | Semantic domain strength chart. |
| `scripts/visualise_occupation_orientation.py` | Top ESCO occupation-orientation chart. |
| `scripts/visualise_clustered_heatmap.py` | Module-to-domain contribution heatmap. |

## RAG and Reporting Scripts

| Script | Purpose |
| --- | --- |
| `scripts/generate_employability_report.py --prepare-only` | Prepares retrieved RAG evidence, prompts and generation metadata without calling Ollama. |
| `scripts/generate_employability_report.py` | Calls Ollama for generic RAG-grounded report generation. |
| `scripts/generate_employability_report.py --mode targeted ...` | Generates or prepares targeted occupation advisor reports. |
| `scripts/export_pdf_report.py` | Exports final XAI/RAG PDF report. |

## Canonical Output Contract

The most important output is:

```text
output/final_student_competency_profile.json
```

It is the stable downstream contract for:

- dashboard rendering;
- visual analytics interpretation;
- RAG evidence retrieval;
- prompt generation;
- PDF export;
- dissertation methodology explanation.

## Recommended Run Commands

Prepare the full deterministic pipeline, visuals and generic RAG prompt:

```powershell
python scripts\run_full_pipeline.py
```

Run the same pipeline and call Ollama for the generic report:

```powershell
python scripts\run_full_pipeline.py --with-llm
```

Prepare targeted RAG evidence for a selected occupation:

```powershell
python scripts\generate_employability_report.py --mode targeted --occupation-label "database administrator" --prepare-only
```

Export the PDF:

```powershell
python scripts\export_pdf_report.py
```

## Frozen Assumptions

- Scores are academic evidence-strength indicators, not competence measurements.
- Bloom is a cognitive-depth evidence signal, not a definitive learning-depth assessment.
- ESCO skills are semantic evidence signals, not verified skills.
- ESCO occupations are orientation signals, not job recommendations.
- RAG generation must use retrieved structured evidence and remain auditable.
- Human review remains required for final interpretation.
