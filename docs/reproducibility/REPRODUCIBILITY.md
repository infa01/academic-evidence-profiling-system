# Reproducibility Guide

This guide describes how to reproduce the project from a clean GitHub clone.

The project is designed as a locally reproducible research prototype. It is not
intended for GitHub Pages deployment because it requires Python, FastAPI, local
files, sentence-transformer models, ESCO lookup files and optional local Ollama
generation.

## 1. Clone the Repository

```powershell
git clone <repo-url>
cd thesis_project_v0.15.4
```

## 2. Create and Activate a Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Add ESCO Data

Download the ESCO classification JSON-LD archive and place it at:

```text
data/esco/esco_classification_jsonld.zip
```

Then build local lookup files:

```powershell
python scripts\build_esco_lookup.py
python scripts\build_esco_interpretation_lookup.py
```

Expected generated files:

```text
data/esco/esco_skill_lookup.json
data/esco/esco_interpretation_lookup.json
```

These files are required for readable ESCO labels, ESCO skill interpretation and
skill-to-occupation relations.

## 5. Prepare Student Input

Option A: use the dashboard:

```powershell
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000/student-input
```

Option B: edit:

```text
data/student_input.json
```

The current sample/test input may use identical grades for testing. A real run
should use the student's actual selected modules and grades.

## 6. Run the Canonical Pipeline

Run deterministic evidence extraction, visual analytics and RAG prompt
preparation:

```powershell
python scripts\run_full_pipeline.py
```

This produces the canonical final profile:

```text
output/final_student_competency_profile.json
```

## 7. Optional Local LLM Generation

Install Ollama and pull a configured model:

```powershell
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama serve
```

The default configuration uses `qwen2.5:7b` with `llama3.1:8b` as fallback.
This choice is based on the local LLM/RAG benchmark in
[../evaluation/LLM_MODEL_BENCHMARK.md](../evaluation/LLM_MODEL_BENCHMARK.md). Additional comparison models
can be pulled when reproducing the benchmark, but are not required for normal
prototype execution.

Generate the generic report:

```powershell
python scripts\run_full_pipeline.py --with-llm
```

Evaluate the generated generic RAG report with lightweight RAGAS-inspired
proxy metrics:

```powershell
python scripts\evaluate_rag_generation.py
```

Expected outputs:

```text
output/rag_evaluation_metrics.json
output/rag_evaluation_metrics.md
```

Prepare targeted occupation evidence without Ollama:

```powershell
python scripts\generate_employability_report.py --mode targeted --occupation-label "database administrator" --prepare-only
```

Generate a targeted report with Ollama:

```powershell
python scripts\generate_employability_report.py --mode targeted --occupation-label "database administrator"
```

## 8. Export PDF

```powershell
python scripts\export_pdf_report.py
```

Expected output:

```text
output/recruiter_ready_xai_report.pdf
```

## 9. Run the Dashboard

```powershell
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000/dashboard
```

## Expected GitHub Contents

The repository should include:

```text
app.py
config/
data/modules.json
data/bloom/
docs/
scripts/
static/
templates/
README.md
INSTALLATION.md
requirements.txt
```

The repository should not include:

```text
data/esco/esco_classification_jsonld.zip
data/esco/esco_skill_lookup.json
data/esco/esco_interpretation_lookup.json
output/
output/charts/
venv/
__pycache__/
```

## Reproducibility Notes

- The first run may download sentence-transformer model weights.
- Local output files are generated under `output/`.
- Ollama is optional if only prompt preparation and RAG evidence are needed.
- Full LLM reports depend on the installed local model and hardware.
- The project should be presented as a local research prototype, not a static web
  deployment.
