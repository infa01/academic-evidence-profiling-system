# Cleanup Audit

This document classifies project files before physical cleanup. The goal is to
avoid breaking the pipeline while making the repository easier to maintain.

## Keep as Core Pipeline

These files are part of the canonical run and should remain easy to find:

- `scripts/run_full_pipeline.py`
- `scripts/methodology_config.py`
- `scripts/bloom_mapper.py`
- `scripts/bloom_semantic_classifier.py`
- `scripts/esco_extractor.py`
- `scripts/semantic_similarity.py`
- `scripts/student_profile.py`
- `scripts/aggregate_profile.py`
- `scripts/enrich_aggregated_profile.py`
- `scripts/calibrate_scores.py`
- `scripts/interpret_esco_concepts.py`
- `scripts/cluster_skills.py`
- `scripts/derive_occupation_orientation.py`
- `scripts/build_final_profile.py`

## Keep as Visual Analytics

- `scripts/visualise_top_skills.py`
- `scripts/visualise_bloom_distribution.py`
- `scripts/visualise_domain_strength.py`
- `scripts/visualise_occupation_orientation.py`
- `scripts/visualise_clustered_heatmap.py`

## Keep as RAG / Reporting

- `scripts/generate_employability_report.py`
- `scripts/export_pdf_report.py`

## Keep as ESCO Setup / Dev Tools

These scripts are useful when rebuilding local ESCO lookup files, but they are
not part of the normal student-profile pipeline:

- `scripts/build_esco_lookup.py`
- `scripts/build_esco_interpretation_lookup.py`

Decision: keep these top-level because installation/reproducibility instructions
call them directly. They are setup scripts, not part of the normal
student-profile pipeline.

## Keep as Developer Inspection Tools

These are outside the core script list and are intended for inspection/debugging:

- `scripts/dev_tools/analyze_results.py`
- `scripts/dev_tools/inspect_esco_dataset.py`
- `scripts/dev_tools/inspect_esco_jsonld.py`

Current status: these scripts now resolve the repository root from their nested
folder location, so they can be run directly without producing incorrect
`scripts/output/...` paths.

## Keep as Application Code

- `app.py`
- `templates/dashboard.html`
- `static/style.css`

## Keep as Methodology Documentation

- `docs/PIPELINE_FREEZE.md`
- `docs/SCORING_METHODOLOGY.md`
- `docs/ESCO_MATCHING_NOISE.md`
- `docs/BLOOM_TAXONOMY_METHODOLOGY.md`
- `docs/RAG_AND_PROMPT_STRATEGY.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/VISUAL_ANALYTICS.md`
- `docs/LIMITATIONS_AND_ETHICS.md`

These docs now form the methodology package for README rewriting, dissertation
methodology sections, presentation planning and poster planning.

## Generated / Ignored Runtime Files

The following are generated and should not be treated as source code:

- `output/*`
- `output/charts/*`
- `__pycache__/`
- `.pytest_cache/`
- model caches

These are already covered by `.gitignore`.

## Immediate Cleanup Recommendations

1. Keep top-level core scripts stable to avoid import/path churn near submission.
2. Keep ESCO setup scripts top-level because they are part of first-time setup.
3. Keep inspection scripts under `scripts/dev_tools/`.
4. Avoid committing generated files from `output/`, caches or local model data.

## Final Script Structure

Current submitted structure:

```text
scripts/
  dev_tools/
  core, setup, visual, RAG and reporting scripts remain top-level
```

This conservative structure is intentional: it keeps the canonical pipeline and
FastAPI subprocess calls simple, while still separating developer-only
inspection scripts.
