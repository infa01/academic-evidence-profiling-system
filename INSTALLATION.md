# Installation Guide

## 1. Create a Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

For Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

## 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 3. Prepare ESCO Data

The project expects local ESCO lookup files in:

```text
data/esco/
```

If the lookup files need to be rebuilt from the ESCO JSON-LD archive, run:

```powershell
python scripts\build_esco_lookup.py
python scripts\build_esco_interpretation_lookup.py
```

More detail is available in:

```text
data/esco/README.md
docs/reproducibility/REPRODUCIBILITY.md
```

## 4. Run the Pipeline

Create a local student input file before running the pipeline:

```powershell
Copy-Item data\student_input.example.json data\student_input.json
```

Run the canonical deterministic pipeline, visual analytics and RAG prompt
preparation:

```powershell
python scripts\run_full_pipeline.py
```

Run the core evidence pipeline only:

```powershell
python scripts\run_full_pipeline.py --skip-visuals --skip-rag
```

## 5. Optional Ollama Setup

Install Ollama from:

```text
https://ollama.com/
```

Download the recommended configured models:

```powershell
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
```

`qwen2.5:7b` is the recommended default model for RAG-grounded report
generation. `llama3.1:8b` is kept as a fallback and quality baseline. Optional
comparison models used during evaluation include `phi3:mini`, `mistral` and
`gemma2:9b`; these are not required to run the application.

Start Ollama:

```powershell
ollama serve
```

Generate the generic report through the pipeline:

```powershell
python scripts\run_full_pipeline.py --with-llm
```

## 6. Start the Dashboard

```powershell
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000/student-input
```

The dashboard is available at:

```text
http://127.0.0.1:8000/dashboard
```

## 7. Export PDF

```powershell
python scripts\export_pdf_report.py
```

If export fails, close any currently open copy of the generated PDF and retry.

## Common Issues

### Ollama is unavailable

Use prepare-only mode when Ollama is not running:

```powershell
python scripts\generate_employability_report.py --prepare-only
```

### Missing charts

Regenerate visual analytics:

```powershell
python scripts\run_full_pipeline.py --skip-rag
```

### Port 8000 is in use

```powershell
uvicorn app:app --reload --port 8001
```

### Empty profile

Check that:

- student input includes selected modules;
- grades and coursework weights are valid;
- ESCO lookup files exist in `data/esco/`;
- the full pipeline completed without errors.
