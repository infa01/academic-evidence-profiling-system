# Technologies, Resources and Tools

This document summarises the main technologies, libraries, datasets, tools and
local resources used in the prototype. It can be used as supporting material for
the dissertation appendix, presentation or reproducibility documentation.

## Development Environment

| Component | Use in project |
| --- | --- |
| Windows desktop environment | Local development, pipeline execution and dashboard testing. |
| Visual Studio Code | Source-code editing, project navigation, terminal execution and Markdown documentation. |
| PowerShell | Running scripts, checking artifacts and executing the local development server. |
| Git / GitHub | Version control and project distribution. |
| Python | Main programming language for the pipeline, backend logic, scoring, analytics and report generation. |

## Backend and Web Application

| Technology | Use in project |
| --- | --- |
| FastAPI | Web backend, dashboard routes, student input handling, report generation routes and PDF export endpoints. |
| Uvicorn | Local ASGI server used to run the FastAPI application. |
| Jinja2 | Server-side HTML templating for the dashboard interface. |
| HTML/CSS | Dashboard layout, XAI panels, evidence cards and visual presentation. |
| python-multipart | Form handling for FastAPI student input and configuration forms. |

## Data Processing and Machine Learning

| Library / Tool | Use in project |
| --- | --- |
| sentence-transformers | Semantic embeddings for Bloom disambiguation, ESCO matching, clustering support and RAG retrieval. |
| all-MiniLM-L6-v2 | Lightweight embedding model used as the main sentence-transformer baseline. |
| scikit-learn | Agglomerative clustering and similarity-related ML utilities. |
| matplotlib | Static chart generation for dashboard visual analytics. |
| requests | HTTP calls to local Ollama endpoints. |
| json / pathlib / subprocess | Standard Python utilities for artifact handling and script orchestration. |

## Taxonomies and Knowledge Resources

| Resource | Use in project |
| --- | --- |
| Revised Bloom's Taxonomy | Cognitive-depth evidence from learning outcome wording. |
| Bloom action verb resources | Rule-based support for initial Bloom classification. |
| ESCO taxonomy | Skill and occupation vocabulary for employability-oriented mapping. |
| ESCO skill lookup | Local preprocessed JSON lookup used by the semantic matching pipeline. |
| ESCO occupation relations | Used to derive occupation-orientation signals from matched skills. |

## Local LLM and RAG Tools

| Component | Use in project |
| --- | --- |
| Ollama | Local LLM runtime for generic and targeted report generation. |
| qwen2.5:7b | Default local LLM after benchmark comparison. |
| llama3.1:8b | Fallback / quality baseline model. |
| phi3:mini | Lightweight model tested during benchmarking. |
| mistral | Additional local model tested during benchmarking. |
| gemma2:9b | Larger local model tested; useful for comparison but more resource-sensitive. |
| Structured JSON retrieval | Section-based retrieval from the final profile, used instead of a full vector database in the current prototype. |

## Reporting and Export

| Library / Tool | Use in project |
| --- | --- |
| ReportLab | PDF report generation. |
| Markdown documentation | Dissertation drafts, methodology notes, appendices, benchmark notes and presentation/poster material. |
| JSON artifacts | Reproducible intermediate and final outputs across the pipeline. |

## Visual Analytics

Generated chart artifacts include:

- `output/charts/top_skills_bar_chart.png`
- `output/charts/bloom_distribution_chart_with_ambiguity.png`
- `output/charts/domain_strength_bar_chart.png`
- `output/charts/occupation_orientation_bar_chart.png`
- `output/charts/clustered_domain_heatmap.png`

These visuals are used to support interpretation of academic evidence signals.
They should not be interpreted as objective measurements of professional
competence.

## Main Python Requirements

The current `requirements.txt` includes:

```text
fastapi
uvicorn
jinja2
python-multipart
requests
sentence-transformers
scikit-learn
matplotlib
reportlab
esco-skill-extractor
```

## Hardware Reference

The local benchmark and development work were carried out on the following
reference machine:

| Component | Specification |
| --- | --- |
| CPU | AMD Ryzen 7 2700X, 8-core, approximately 3.7 GHz |
| Motherboard | X470 Aorus Ultra Gaming |
| RAM | 16 GB DDR4 3200 MHz |
| GPU | NVIDIA GeForce GTX 1050 Ti 4 GB Windforce OC |

This hardware context is relevant because local LLM latency and feasibility
depend strongly on available CPU, RAM, GPU memory and quantisation.

## Project-Specific Scripts

| Script / Directory | Purpose |
| --- | --- |
| `scripts/run_full_pipeline.py` | Runs the canonical evidence pipeline. |
| `scripts/bloom_mapper.py` | Adds Bloom evidence to learning outcomes. |
| `scripts/semantic_similarity.py` | Computes ESCO semantic similarity and filtering. |
| `scripts/student_profile.py` | Builds raw student skill occurrences. |
| `scripts/build_final_profile.py` | Produces the final structured JSON profile. |
| `scripts/generate_employability_report.py` | Prepares RAG evidence and generates generic/targeted reports. |
| `scripts/evaluate_rag_generation.py` | Computes lightweight RAGAS-inspired proxy metrics. |
| `scripts/evaluate_prototype.py` | Checks expected artifacts and prototype outputs. |
| `scripts/dev_tools/` | Diagnostic and inspection scripts for development use. |

## Dissertation Framing

These technologies are not presented as isolated tools. They support the core
methodological aim of the project:

> to transform academic learning outcomes, grades and module metadata into
> structured, explainable evidence that can support employability reflection and
> RAG-grounded report generation.

