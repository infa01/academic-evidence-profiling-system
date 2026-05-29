# System Architecture

This document describes the current system architecture for the explainable
academic evidence profiling prototype. The architecture is pipeline-oriented:
each stage produces transparent intermediate artifacts, and downstream
components consume the canonical final structured profile.

## 1. End-to-End Pipeline Architecture

```mermaid
flowchart TD
    A["Student Input\nselected modules, grades, coursework weights"] --> B["Module Dataset\nlearning outcomes + module levels"]
    B --> C["Bloom Cognitive-Depth Analysis\nrule + semantic classifier"]
    C --> D["ESCO Skill Extraction\ncandidate skills per learning outcome"]
    D --> E["Semantic Similarity Filtering\nmatch scores + quality labels"]
    E --> F["Raw Student Skill Evidence\nLO + ESCO + grade + Bloom"]
    F --> G["Academic Evidence Scoring\ngrade x similarity x Bloom x module level"]
    G --> H["Aggregated ESCO Skill Profile\nskill scores + XAI components"]
    H --> I["ESCO Concept Interpretation\nskill type, reuse level, occupation links"]
    I --> J["Semantic Skill Domains\nembedding-based clustering"]
    I --> K["ESCO Occupation Orientation\nprioritised + weak/noise signals"]
    J --> L["Final Structured Evidence Profile JSON"]
    K --> L
    L --> M["Visual Analytics\ncharts for dashboard and PDF"]
    L --> N["Controlled RAG Retrieval\nevidence chunks by section"]
    N --> O["Generic Employability Prompt"]
    N --> P["Targeted Occupation Prompt"]
    O --> Q["Local LLM Generation\nOllama optional"]
    P --> Q
    Q --> R["Generated Reports\nstudent-facing guidance"]
    L --> S["FastAPI Dashboard"]
    M --> S
    R --> S
    N --> S
    L --> T["XAI/RAG PDF Export"]
    M --> T
    R --> T
    N --> T
```

### Interpretation

The pipeline is designed to avoid a black-box workflow. Each major inference
stage stores structured evidence and methodology metadata so that the dashboard,
RAG prompts and PDF export can explain how outputs were produced.

## 2. Evidence Model / XAI Architecture

```mermaid
flowchart LR
    A["Learning Outcome Evidence"] --> B["Bloom Evidence\nlevel, method, confidence,\nreliability, ambiguity"]
    A --> C["ESCO Skill Evidence\nsimilarity score,\nmatch quality, threshold"]
    A --> D["Module Context\nmodule code, title, level"]
    A --> E["Student Performance Signal\nfinal grade + assessment structure"]

    B --> F["Skill Occurrence Evidence"]
    C --> F
    D --> F
    E --> F

    F --> G["Aggregated Skill Evidence\nscore, modules, XAI components"]
    G --> H["Semantic Skill Domains\ncluster label + member skills"]
    G --> I["ESCO Occupation Orientation\nsupporting skills + relation types"]

    H --> J["Final Structured Profile"]
    I --> J
    G --> J
    J --> K["Methodology Snapshot\nweights, thresholds, limitations"]
    J --> L["RAG Evidence Chunks"]
    J --> M["Dashboard XAI Panels"]
    J --> N["PDF XAI Tables"]
```

### Interpretation

The final profile is not only a list of ranked skills. It is an evidence model
that preserves traceability from learning outcomes to Bloom, ESCO, scoring,
semantic domains and occupation-orientation signals.

The most important artifact is:

```text
output/final_student_competency_profile.json
```

## 3. RAG Architecture

```mermaid
flowchart TD
    A["Final Structured Evidence Profile"] --> B["Evidence Chunk Builder\nskills, domains, occupations,\nmethodology notes"]
    B --> C["RAG Evidence Chunks"]
    C --> D["Section-Based Retrieval\nsentence-transformer cosine similarity"]

    D --> E["Generic Sections\nsummary, skills, career signals,\nCV support, development, limitations"]
    D --> F["Targeted Sections\nselected occupation, supporting skills,\nCV translation, development plan"]

    E --> G["Generic Prompt\nmethodology + retrieved evidence + rules"]
    F --> H["Targeted Prompt\nselected occupation + constrained evidence"]

    G --> I["Local LLM via Ollama\noptional generation"]
    H --> I

    I --> J["Generic Employability Report"]
    I --> K["Targeted Occupation Advisor Report"]

    D --> L["Retrieved Evidence JSON"]
    G --> M["Prompt Transparency Files"]
    H --> M
    J --> N["Generation Metadata\nrequired sections, forbidden phrases,\nwarning checks, quality gate"]
    K --> N
```

### Interpretation

The RAG layer is controlled rather than fully autonomous. The system retrieves
specific evidence for predefined report sections and then asks the LLM to write
within strict evidence boundaries. This improves auditability and supports
responsible output framing.

This is structured runtime retrieval, not a persistent vector database
deployment. Evidence chunks are generated from the final profile for each run,
embedded and retrieved by report section. A vector database would become more
appropriate for a larger system with many profiles, larger document corpora,
uploaded CVs or dynamic user queries.

## 4. Runtime Components

```mermaid
flowchart TB
    A["FastAPI app.py"] --> B["Student Input Form"]
    B --> C["Pipeline Runner\nscripts/run_full_pipeline.py"]
    C --> D["Generated Output Files"]
    D --> E["Dashboard Template\ntemplates/dashboard.html"]
    D --> F["Static Charts\noutput/charts"]
    D --> G["PDF Export\nscripts/export_pdf_report.py"]
    D --> H["RAG/Prompt Generator\nscripts/generate_employability_report.py"]
    H --> I["Ollama Local LLM\noptional"]
    I --> D
```

### Interpretation

The dashboard is an orchestration and presentation layer. The evidence pipeline
itself is implemented as standalone Python scripts so that the project remains
auditable and reproducible outside the web interface.

## 5. Main Artifacts

| Artifact | Purpose |
| --- | --- |
| `data/student_input.json` | Student-selected modules and assessment data. |
| `data/modules_with_bloom.json` | Module learning outcomes enriched with Bloom evidence. |
| `output/modules_with_bloom_esco_filtered.json` | Bloom + ESCO skill matches after semantic filtering. |
| `output/student_skill_profile.json` | Raw student skill occurrence evidence. |
| `output/student_skill_profile_calibrated.json` | Aggregated and calibrated skill evidence. |
| `output/student_skill_clusters.json` | Semantic skill domains. |
| `output/student_occupation_orientation.json` | ESCO occupation-orientation signals. |
| `output/final_student_competency_profile.json` | Canonical structured evidence profile. |
| `output/rag_retrieved_evidence.json` | Retrieved evidence for generic RAG generation. |
| `output/targeted_rag_retrieved_evidence.json` | Retrieved evidence for selected occupation generation. |
| `output/rag_generation_metadata.json` | Generic generation quality metadata. |
| `output/targeted_rag_generation_metadata.json` | Targeted generation quality metadata. |
| `output/recruiter_ready_xai_report.pdf` | Final XAI/RAG PDF export. |

## 6. Design Rationale

The architecture prioritises:

- **Traceability:** outputs can be traced back to modules and learning outcomes.
- **Explainability:** scores expose their components and methodology assumptions.
- **Conservative interpretation:** outputs avoid claims of professional mastery.
- **RAG grounding:** LLM generation is constrained by retrieved structured evidence.
- **Local execution:** the prototype can run with a local Ollama model.
- **Modularity:** each stage can be inspected, rerun or replaced independently.

## 7. Architectural Limitations

- The pipeline is a research prototype, not a production deployment.
- ESCO and Bloom stages depend on text quality and semantic matching.
- Local LLM output still requires human review.
- The current pipeline is file-based and runtime-retrieval based rather than
  database-backed.
- Full expert validation is outside the current implementation scope.
