# Explainable Academic Evidence Profiling with ESCO, Bloom and RAG

This project is a BSc Computer Science dissertation prototype for building an
explainable academic evidence profile from university module learning outcomes,
student grades, Revised Bloom's Taxonomy, ESCO skills/occupations and
RAG-grounded local LLM generation.

The system does **not** certify professional competence or make automated career
decisions. It creates a transparent academic evidence profile that can support
career reflection, CV positioning and role exploration.

## What the System Does

- Reads Computer Science module learning outcomes.
- Classifies learning outcomes using a hybrid Bloom taxonomy approach.
- Extracts and filters ESCO skill matches using semantic similarity.
- Combines student performance signals, semantic similarity, Bloom cognitive
  depth and module level weighting into academic evidence scores.
- Aggregates repeated ESCO skill evidence into a structured student profile.
- Derives semantic skill domains through clustering.
- Derives ESCO occupation-orientation signals from skill-to-occupation links.
- Builds a canonical final JSON profile for dashboard, RAG, visuals and PDF.
- Generates visual analytics for interpretability.
- Prepares generic and targeted RAG prompts for local LLM generation.
- Exports an XAI/RAG PDF report.

## What the System Does Not Do

- It does not measure professional competence.
- It does not guarantee job suitability.
- It does not make hiring or admissions decisions.
- It does not treat ESCO occupation links as job recommendations.
- It does not treat LLM output as the source of truth.
- It does not remove the need for human review.

## Canonical Pipeline

```text
Student Input
-> Module Learning Outcomes
-> Bloom Cognitive-Depth Evidence
-> ESCO Skill Extraction
-> Semantic Similarity Filtering + Match Quality
-> Student Performance Evidence
-> Academic Evidence Scoring
-> Aggregated ESCO Skill Profile
-> ESCO Concept Interpretation
-> Semantic Skill Domains
-> ESCO Occupation-Orientation Signals
-> Final Structured Evidence Profile JSON
-> Visual Analytics
-> Controlled RAG Retrieval
-> Generic / Targeted LLM Generation
-> Dashboard + PDF Export
```

The frozen pipeline definition is documented in
[docs/reproducibility/PIPELINE_FREEZE.md](docs/reproducibility/PIPELINE_FREEZE.md).

System architecture diagrams are documented in
[docs/reproducibility/SYSTEM_ARCHITECTURE.md](docs/reproducibility/SYSTEM_ARCHITECTURE.md).

## Core Methodology

### Academic Evidence Scoring

The occurrence-level score is:

```text
occurrence_evidence_score =
    grade_weight
    x semantic_similarity_score
    x bloom_weight
    x module_level_weight
```

Scores are theoretical academic evidence-strength indicators used for ranking,
explainability and RAG retrieval. They are not validated measurements of
professional ability.

Details: [docs/methodology/SCORING_METHODOLOGY.md](docs/methodology/SCORING_METHODOLOGY.md)

### Bloom Taxonomy

Bloom is used as a cognitive-depth evidence signal. The classifier combines
action-verb mapping with semantic disambiguation and exposes confidence,
ambiguity and reliability metadata.

Details:
[docs/methodology/BLOOM_TAXONOMY_METHODOLOGY.md](docs/methodology/BLOOM_TAXONOMY_METHODOLOGY.md)

### ESCO Matching

ESCO matching is treated as semantic evidence extraction, not definitive skill
verification. The system exposes similarity scores, match-quality labels,
supporting-skill traces and weak/noise occupation categories.

Details: [docs/methodology/ESCO_MATCHING_NOISE.md](docs/methodology/ESCO_MATCHING_NOISE.md)

### RAG and LLM Generation

The LLM receives retrieved structured evidence chunks rather than the whole raw
project output. Generic and targeted generation modes store prompt files,
retrieved evidence and generation quality metadata.

The generated generic report can also be checked with lightweight
RAGAS-inspired proxy metrics for context precision, section relevance,
faithfulness, answer relevance and evidence mention coverage.

Details: [docs/methodology/RAG_AND_PROMPT_STRATEGY.md](docs/methodology/RAG_AND_PROMPT_STRATEGY.md)

Visual analytics and ethics/limitations are documented in:

- [docs/methodology/VISUAL_ANALYTICS.md](docs/methodology/VISUAL_ANALYTICS.md)
- [docs/methodology/LIMITATIONS_AND_ETHICS.md](docs/methodology/LIMITATIONS_AND_ETHICS.md)

## Main Outputs

The most important output is:

```text
output/final_student_competency_profile.json
```

This is the canonical structured evidence contract used by:

- the dashboard;
- visual analytics;
- RAG retrieval;
- prompt generation;
- PDF export;
- dissertation methodology explanation.

Other useful outputs:

```text
output/rag_retrieved_evidence.json
output/rag_generation_metadata.json
output/employability_prompt.txt
output/employability_report.txt
output/rag_evaluation_metrics.json
output/rag_evaluation_metrics.md
output/targeted_rag_retrieved_evidence.json
output/targeted_rag_generation_metadata.json
output/targeted_occupation_prompt.txt
output/targeted_occupation_report.txt
output/academic_evidence_profile_report.pdf
output/charts/
```

Generated outputs are ignored by Git.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Optional local LLM setup:

```powershell
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama serve
```

The default LLM model is configured in:

```text
config/llm_config.json
```

The recommended default model is `qwen2.5:7b`, selected from the local
LLM/RAG benchmark as the best quality/runtime balance on the tested hardware.
`llama3.1:8b` is kept as the configured fallback and quality baseline. The full
model comparison is documented in
[docs/evaluation/LLM_MODEL_BENCHMARK.md](docs/evaluation/LLM_MODEL_BENCHMARK.md).

Full reproducibility instructions are available in
[docs/reproducibility/REPRODUCIBILITY.md](docs/reproducibility/REPRODUCIBILITY.md).

ESCO local data setup is documented in
[data/esco/README.md](data/esco/README.md).

## Running the Project

Run the canonical deterministic pipeline, visuals and RAG preparation:

```powershell
Copy-Item data\student_input.example.json data\student_input.json
```

```powershell
python scripts\run_full_pipeline.py
```

Run the core evidence pipeline only:

```powershell
python scripts\run_full_pipeline.py --skip-visuals --skip-rag
```

Run the pipeline and call Ollama for the generic report:

```powershell
python scripts\run_full_pipeline.py --with-llm
```

Prepare targeted RAG evidence for an occupation:

```powershell
python scripts\generate_employability_report.py --mode targeted --occupation-label "database administrator" --prepare-only
```

Generate a targeted report with Ollama:

```powershell
python scripts\generate_employability_report.py --mode targeted --occupation-label "database administrator"
```

Export the PDF:

```powershell
python scripts\export_pdf_report.py
```

## Running the Dashboard

Start FastAPI:

```powershell
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000/student-input
```

The dashboard is available after submitting student input:

```text
http://127.0.0.1:8000/dashboard
```

Dashboard features:

- final structured evidence profile summary;
- learning outcome evidence trace;
- ranked ESCO skill evidence;
- semantic skill domains;
- ESCO occupation-orientation signals;
- RAG grounding evidence;
- generic employability report;
- targeted occupation advisor report;
- visual analytics;
- PDF export.

## Repository Structure

```text
config/                 Local LLM and prompt configuration
data/                   Source modules, Bloom taxonomy and local input JSON
data/esco/              Local ESCO lookup artifacts, ignored except .gitkeep
docs/                   Public methodology, evaluation and reproducibility docs
docs/evaluation/        Benchmark and evaluation summaries
docs/methodology/       Methodology, limitations and visual analytics notes
docs/reproducibility/   Setup, architecture and reproducibility notes
output/                 Generated profiles, reports, metadata and charts
scripts/                Pipeline, visual analytics, RAG and reporting scripts
scripts/dev_tools/      Developer inspection tools
static/                 CSS and static assets
templates/              FastAPI/Jinja dashboard templates
app.py                  FastAPI application
```

Private dissertation drafts, generated outputs and local working notes are
excluded from the public release repository.

## Developer Notes

Useful developer scripts:

```powershell
python scripts\dev_tools\analyze_results.py
python scripts\dev_tools\inspect_esco_dataset.py
python scripts\dev_tools\inspect_esco_jsonld.py
```

Prototype evaluation:

```powershell
python scripts\evaluate_prototype.py
```

Evaluate the generated generic RAG report:

```powershell
python scripts\evaluate_rag_generation.py
```

This produces:

- `output/prototype_evaluation_report.json`
- `output/prototype_evaluation_report.md`

ESCO setup scripts:

```powershell
python scripts\build_esco_lookup.py
python scripts\build_esco_interpretation_lookup.py
```

These setup scripts are useful when rebuilding local ESCO lookup files, but they
are not part of the normal student-profile pipeline.

## Limitations

- The scoring system is theoretical and designed for academic evidence ranking.
- Bloom classification from learning outcome text is approximate.
- ESCO semantic matching can contain borderline or noisy links.
- ESCO occupation outputs are orientation signals, not recommendations.
- RAG reduces unsupported generation but does not eliminate all LLM risks.
- Human review is required for final interpretation.

## Dissertation Framing

A concise way to describe the project:

> This system builds an explainable academic evidence profile from module
> learning outcomes and student performance signals. It aligns learning outcomes
> with Bloom cognitive-depth evidence and ESCO skill/occupation terminology,
> then uses controlled RAG to generate auditable employability guidance without
> presenting the output as a professional competence assessment or automated
> career decision.
