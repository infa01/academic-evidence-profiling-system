"""
app.py

Main FastAPI application for the Academic Evidence Profiling System.

This file orchestrates:
- dashboard rendering,
- student input processing,
- pipeline execution,
- local LLM report generation,
- PDF export,
- and explainable AI output presentation.
"""

from pathlib import Path
from datetime import datetime
import json
import time

from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import subprocess
from fastapi.responses import RedirectResponse

from fastapi.responses import FileResponse


# =========================================================
# Core Paths and Global State
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
STUDENT_INPUT_PATH = DATA_DIR / "student_input.json"
LLM_CONFIG_PATH = BASE_DIR / "config" / "llm_config.json"
PROFILE_PATH = BASE_DIR / "output" / "student_skill_profile_calibrated.json"
FINAL_PROFILE_PATH = BASE_DIR / "output" / "final_student_competency_profile.json"
CLUSTERS_PATH = BASE_DIR / "output" / "student_skill_clusters.json"
ESCO_SKILL_LOOKUP_PATH = BASE_DIR / "data" / "esco" / "esco_skill_lookup.json"
MODULES_WITH_ESCO_PATH = BASE_DIR / "output" / "modules_with_bloom_esco_filtered.json"
OCCUPATION_ORIENTATION_PATH = BASE_DIR / "output" / "student_occupation_orientation.json"
RAG_RETRIEVED_EVIDENCE_PATH = BASE_DIR / "output" / "rag_retrieved_evidence.json"
TARGETED_RAG_RETRIEVED_EVIDENCE_PATH = (
    BASE_DIR / "output" / "targeted_rag_retrieved_evidence.json"
)
TARGETED_OCCUPATION_REPORT_PATH = OUTPUT_DIR / "targeted_occupation_report.txt"
RAG_GENERATION_METADATA_PATH = OUTPUT_DIR / "rag_generation_metadata.json"
TARGETED_RAG_GENERATION_METADATA_PATH = (
    OUTPUT_DIR / "targeted_rag_generation_metadata.json"
)
RAG_EVALUATION_METRICS_PATH = OUTPUT_DIR / "rag_evaluation_metrics.json"
TARGETED_RAG_EVALUATION_METRICS_PATH = (
    OUTPUT_DIR / "targeted_rag_evaluation_metrics.json"
)

CHARTS_DIR = OUTPUT_DIR / "charts"

CHART_FILES = {
    "top_skills": "top_skills_bar_chart.png",
    "domain_strength": "domain_strength_bar_chart.png",
    "occupation_orientation": "occupation_orientation_bar_chart.png",
    "bloom": "bloom_distribution_chart_with_ambiguity.png",
    "heatmap": "clustered_domain_heatmap.png"
}

OCCUPATION_SIGNAL_DISPLAY_LIMIT = 12


# In-memory session state (non-persistent)
SESSION_RUNS = []

# Latest pipeline/runtime error shown in dashboard
LAST_PIPELINE_ERROR = None

# Latest student input validation error
LAST_INPUT_ERROR = None


# =========================================================
# FastAPI Application Setup
# =========================================================
app = FastAPI(
    title="Academic Evidence Profiling System"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

app.mount(
    "/charts",
    StaticFiles(directory=OUTPUT_DIR / "charts"),
    name="charts"
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

templates.env.cache = None

# =========================================================
# Utility Functions
# =========================================================
def safe_load_json(path, fallback):
    try:
        if not path.exists():
            return fallback

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        print(f"Invalid JSON file: {path}")
        return fallback

    except Exception as error:
        print(f"Could not load JSON file: {path}")
        print(error)
        return fallback

def safe_load_text(path, fallback=""):
    try:
        if not path.exists():
            return fallback

        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    except Exception as error:
        print(f"Could not load text file: {path}")
        print(error)
        return fallback
    
def load_json_from_path(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_to_path(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def validate_grade(value, field_name):
    grade = parse_float(value, field_name)

    if grade < 0 or grade > 100:
        raise ValueError(f"{field_name} must be between 0 and 100.")

    return grade


def validate_weight(value, field_name):
    weight = parse_float(value, field_name)

    if weight <= 0 or weight > 1:
        raise ValueError(f"{field_name} must be greater than 0 and at most 1.")

    return weight

def get_chart_status():
    chart_status = {}

    for chart_key, filename in CHART_FILES.items():
        chart_path = CHARTS_DIR / filename

        chart_status[chart_key] = {
            "filename": filename,
            "exists": chart_path.exists()
        }

    return chart_status


def build_raw_occurrence_lookup(final_profile):
    lookup = {}

    raw_occurrences = final_profile.get(
        "competencies",
        {}
    ).get(
        "raw_occurrences",
        []
    )

    for occurrence in raw_occurrences:
        key = (
            occurrence.get("module_code"),
            occurrence.get("learning_outcome_id"),
            occurrence.get("esco_uri")
        )

        lookup[key] = occurrence

    return lookup


def calculate_occurrence_evidence_score(occurrence, final_profile):
    methodology = final_profile.get("methodology", {})

    bloom_weights = methodology.get("bloom_weights", {})
    module_level_weights = methodology.get("module_level_weights", {})

    cognitive_level = occurrence.get("cognitive_level", "Unknown")
    module_code = occurrence.get("module_code", "")
    module_level = module_code[2] if len(module_code) >= 3 else "Unknown"

    grade_weight = occurrence.get("competency_score", 0)
    similarity_score = occurrence.get("similarity_score", 0)
    bloom_weight = bloom_weights.get(cognitive_level, bloom_weights.get("Unknown", 1))
    module_level_weight = module_level_weights.get(module_level, 1)

    evidence_score = (
        grade_weight *
        similarity_score *
        bloom_weight *
        module_level_weight
    )

    return {
        "occurrence_evidence_score": round(evidence_score, 4),
        "grade_weight": grade_weight,
        "bloom_weight": bloom_weight,
        "module_level_weight": module_level_weight,
        "formula": (
            f"{grade_weight} x {similarity_score} x "
            f"{bloom_weight} x {module_level_weight}"
        )
    }

def load_llm_config():
    return safe_load_json(
        LLM_CONFIG_PATH,
        {
            "provider": "ollama",
            "model": "qwen2.5:7b",
            "fallback_model": "llama3.1:8b",
            "temperature": 0.2,
            "num_predict": 900,
            "request_timeout_seconds": 300
        }
    )

def save_llm_config(config):
    save_json_to_path(config, LLM_CONFIG_PATH)

# =========================================================
# Suggested Role Mapping
# =========================================================
ROLE_MAPPING = {
    "Database Technologies": [
        "Junior Database Developer",
        "Junior Data Analyst",
        "Database Support Assistant"
    ],
    "Artificial Intelligence and Data Analytics": [
        "Junior AI Assistant",
        "Junior Data Analyst",
        "Machine Learning Intern"
    ],
    "Software Development and Documentation": [
        "Junior Software Developer",
        "Technical Documentation Assistant",
        "Application Support Assistant"
    ],
    "Web Technologies": [
        "Junior Web Developer",
        "Frontend Developer Intern",
        "Web Application Support Assistant"
    ],
    "Cyber Security": [
        "Junior Cyber Security Analyst",
        "SOC Analyst Intern",
        "Information Security Assistant"
    ],
    "Networks and Systems": [
        "Junior Network Technician",
        "IT Support Technician",
        "Systems Support Assistant"
    ],
    "General Competency Domain": [
        "Junior IT Support Assistant",
        "Technology Graduate Trainee",
        "Software Support Assistant"
    ]
}

# =========================================================
# Pipeline Execution
# =========================================================
def run_pipeline_safely():
    global LAST_PIPELINE_ERROR

    try:
        # Execute the full academic evidence profiling pipeline locally
        result = subprocess.run(
            [
                "python",
                "scripts/run_full_pipeline.py"
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            LAST_PIPELINE_ERROR = (
                "The academic evidence profiling pipeline could not be completed. "
                "Please review the details below:\n\n"
                f"{result.stderr}"
            )

            print("Pipeline failed:")
            print(result.stderr)

            return False

        LAST_PIPELINE_ERROR = None

        print(result.stdout)

        return True

    except Exception as error:
        LAST_PIPELINE_ERROR = (
            "An unexpected error occurred while running the academic evidence profiling pipeline.\n\n"
            f"{str(error)}"
        )

        print("Unexpected pipeline error:")
        print(error)

        return False


# =========================================================
# Application Routes
# =========================================================
@app.get("/")
def root():
    return RedirectResponse(
        url="/student-input",
        status_code=303
    )

@app.get("/dashboard")
def dashboard(request: Request):
    llm_config = load_llm_config()

    student_input = safe_load_json(
        STUDENT_INPUT_PATH,
        {}
    )

    calibrated_profile = safe_load_json(
        PROFILE_PATH,
        {
            "student_id": "student_001",
            "aggregated_skills": [],
            "calibration": {}
        }
    )

    final_profile = safe_load_json(
        FINAL_PROFILE_PATH,
        {
            "metadata": {
                "profile_schema_version": "-",
                "profile_type": "explainable_academic_evidence_profile"
            },
            "student": {
                "student_id": calibrated_profile.get("student_id", "student_001")
            },
            "methodology": {},
            "learning_outcome_evidence": [],
            "competencies": {
                "raw_occurrences": [],
                "calibrated": []
            },
            "semantic_domains": [],
            "rag": {
                "evidence_chunks": []
            }
        }
    )

    raw_occurrence_lookup = build_raw_occurrence_lookup(final_profile)

    clusters = safe_load_json(
        CLUSTERS_PATH,
        {
            "student_id": "student_001",
            "clusters": []
        }
    )

    modules_with_esco = safe_load_json(
        MODULES_WITH_ESCO_PATH,
        {
            "modules": []
        }
    )

    module_esco_skill_groups = []

    for module in modules_with_esco.get("modules", []):
        module_code = module.get("module_code", "Unknown Module")
        module_title = module.get("module_title", module.get("title", ""))

        module_skills = []

        for lo in module.get("learning_outcomes", []):
            lo_code = lo.get("lo_id", lo.get("learning_outcome_id", "Unknown LO"))
            lo_text = lo.get("text", "")

            bloom = lo.get("bloom", {})

            esco_data = lo.get("esco", {})
            filtered_skills = esco_data.get("skills", esco_data.get("filtered_skills", []))

            for skill in filtered_skills:
                full_esco_text = skill.get("name", "Unknown Skill")

                esco_skill_name = skill.get("display_title", skill.get("preferred_label", full_esco_text))

                occurrence_key = (
                    module_code,
                    lo_code,
                    skill.get("uri", "-")
                )

                raw_occurrence = raw_occurrence_lookup.get(
                    occurrence_key,
                    {}
                )

                occurrence_scoring = calculate_occurrence_evidence_score(
                    raw_occurrence,
                    final_profile
                ) if raw_occurrence else {}

                module_skills.append({
                    "module_code": module_code,
                    "module_title": module_title,
                    "learning_outcome_id": lo_code,
                    "learning_outcome_text": lo_text,

                    "esco_skill_name": esco_skill_name,
                    "preferred_label": skill.get("name", "Unknown Skill"),
                    "full_esco_text": full_esco_text,
                    "esco_uri": skill.get("uri", "-"),
                    "similarity_score": skill.get("similarity_score", "-"),
                    "semantic_match_quality": skill.get(
                        "semantic_match_quality",
                        "-"
                    ),
                    "semantic_match_note": skill.get("semantic_match_note", "-"),
                    "candidate_rank_by_similarity": skill.get(
                        "candidate_rank_by_similarity",
                        "-"
                    ),
                    "occurrence_evidence_score": occurrence_scoring.get(
                        "occurrence_evidence_score",
                        "-"
                    ),
                    "grade_weight": occurrence_scoring.get("grade_weight", "-"),
                    "bloom_weight": occurrence_scoring.get("bloom_weight", "-"),
                    "module_level_weight": occurrence_scoring.get(
                        "module_level_weight",
                        "-"
                    ),
                    "occurrence_formula": occurrence_scoring.get("formula", "-"),

                    "bloom_level": bloom.get("cognitive_level", "Unknown"),
                    "bloom_method": bloom.get("method", "Unknown"),
                    "bloom_rule": bloom.get("rule", "Unknown"),
                    "primary_action_verb": bloom.get("primary_action_verb", "-"),
                    "matched_verbs": bloom.get("matched_verbs", []),
                    "candidate_levels_from_verbs": bloom.get("candidate_levels_from_verbs", []),
                    "bloom_confidence": bloom.get("bloom_confidence", "-"),
                    "score_margin": bloom.get("score_margin", "-"),
                    "is_bloom_near_tie": bloom.get("is_near_tie", False),
                    "near_tie_margin_threshold": bloom.get(
                        "near_tie_margin_threshold",
                        "-"
                    ),
                    "second_bloom_candidate": bloom.get(
                        "second_bloom_candidate",
                        {}
                    ),
                    "bloom_confidence_status": bloom.get("confidence_status", "-"),
                    "bloom_classification_reliability": bloom.get(
                        "classification_reliability",
                        "-"
                    ),
                    "bloom_classification_reliability_note": bloom.get(
                        "classification_reliability_note",
                        "-"
                    ),
                    "bloom_ambiguity_status": bloom.get("ambiguity_status", "-"),
                    "bloom_evidence_role": bloom.get("bloom_evidence_role", "-"),
                    "bloom_interpretation_note": bloom.get("interpretation_note", "-"),
                    "top_bloom_candidates": bloom.get("top_bloom_candidates", [])
                })

        module_esco_skill_groups.append({
            "module_code": module_code,
            "module_title": module_title,
            "skills": module_skills,
            "skill_count": len(module_skills)
        })

    occupation_orientation = safe_load_json(
        OCCUPATION_ORIENTATION_PATH,
        {
            "student_id": "student_001",
            "top_occupation_orientations": [],
            "prioritised_occupation_orientations": [],
            "all_occupation_orientations": [],
            "weak_or_possible_noise_signals": []
        }
    )

    rag_retrieved_evidence = safe_load_json(
        RAG_RETRIEVED_EVIDENCE_PATH,
        {}
    )

    targeted_rag_retrieved_evidence = safe_load_json(
        TARGETED_RAG_RETRIEVED_EVIDENCE_PATH,
        {}
    )

    rag_generation_metadata = safe_load_json(
        RAG_GENERATION_METADATA_PATH,
        {}
    )

    targeted_rag_generation_metadata = safe_load_json(
        TARGETED_RAG_GENERATION_METADATA_PATH,
        {}
    )

    rag_evaluation_metrics = safe_load_json(
        RAG_EVALUATION_METRICS_PATH,
        {}
    )

    targeted_rag_evaluation_metrics = safe_load_json(
        TARGETED_RAG_EVALUATION_METRICS_PATH,
        {}
    )

    # Extract unique semantic domains for dashboard summaries
    unique_domains = []
    seen_domains = set()

    for cluster in clusters.get("clusters", []):
        domain = cluster.get("cluster_label", "Unknown")

        if domain not in seen_domains:
            unique_domains.append(domain)
            seen_domains.add(domain)

    unique_domains = [
        domain
        for domain in unique_domains
        if domain != "General Competency Domain"
    ]

    suggested_roles = []

    for domain in unique_domains:
        roles = ROLE_MAPPING.get(
            domain,
            ["Technology Graduate Trainee"]
        )

        for role in roles:
            if role not in suggested_roles:
                suggested_roles.append(role)

    suggested_roles = suggested_roles[:4]

    top_occupation_signals = occupation_orientation.get(
        "top_occupation_orientations",
        []
    )[:OCCUPATION_SIGNAL_DISPLAY_LIMIT]

    final_profile_summary = {
        "schema_version": final_profile.get("metadata", {}).get(
            "profile_schema_version",
            "-"
        ),
        "learning_outcome_count": len(
            final_profile.get("learning_outcome_evidence", [])
        ),
        "raw_occurrence_count": len(
            final_profile.get("competencies", {}).get("raw_occurrences", [])
        ),
        "calibrated_skill_count": len(
            final_profile.get("competencies", {}).get("calibrated", [])
        ),
        "semantic_domain_count": len(
            final_profile.get("semantic_domains", [])
        ),
        "rag_chunk_count": len(
            final_profile.get("rag", {}).get("evidence_chunks", [])
        ),
        "retrieved_section_count": len(rag_retrieved_evidence)
    }

    report_path = OUTPUT_DIR / "employability_report.txt"

    employability_report = safe_load_text(
        report_path,
        "No employability report has been generated yet."
    )

    targeted_occupation_report = safe_load_text(
        TARGETED_OCCUPATION_REPORT_PATH,
        "No targeted occupation report has been generated yet."
    )

    llm_report_warning = None

    # Detect common LLM failure or fallback outputs
    warning_markers = [
        "LLM REPORT GENERATION WARNING",
        "I don't see any provided evidence",
        "No employability report has been generated yet."
    ]

    if any(marker in employability_report for marker in warning_markers):
        llm_report_warning = (
            "The employability report may not have been generated correctly. "
            "The academic evidence profile and analytics may still be available, but the "
            "LLM output should be reviewed or regenerated."
        )

    chart_status = get_chart_status()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "profile": calibrated_profile,
            "final_profile": final_profile,
            "final_profile_summary": final_profile_summary,
            "clusters": clusters,
            "occupation_orientation": occupation_orientation,
            "top_occupation_signals": top_occupation_signals,
            "rag_retrieved_evidence": rag_retrieved_evidence,
            "targeted_rag_retrieved_evidence": targeted_rag_retrieved_evidence,
            "rag_generation_metadata": rag_generation_metadata,
            "targeted_rag_generation_metadata": targeted_rag_generation_metadata,
            "rag_evaluation_metrics": rag_evaluation_metrics,
            "targeted_rag_evaluation_metrics": targeted_rag_evaluation_metrics,
            "module_esco_skill_groups": module_esco_skill_groups,
            "report": employability_report,
            "targeted_occupation_report": targeted_occupation_report,
            "llm_config": llm_config,
            "student_input": student_input,
            "cache_buster": int(time.time()),
            "session_runs": SESSION_RUNS,
            "pipeline_error": LAST_PIPELINE_ERROR,
            "unique_domains": unique_domains,
            "suggested_roles": suggested_roles,
            "llm_report_warning": llm_report_warning,
            "chart_status": chart_status
        }
    )

@app.post("/set-llm-model")
async def set_llm_model(request: Request):
    form = await request.form()

    selected_model = form.get("llm_model")

    config = load_llm_config()
    config["model"] = selected_model

    save_llm_config(config)

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )

@app.get("/api/profile")
def get_profile():
    return safe_load_json(
        PROFILE_PATH,
        {
            "student_id": "student_001",
            "aggregated_skills": [],
            "calibration": {}
        }
    )


@app.get("/api/final-profile")
def get_final_profile():
    return safe_load_json(
        FINAL_PROFILE_PATH,
        {
            "metadata": {
                "profile_type": "explainable_academic_evidence_profile"
            },
            "student": {
                "student_id": "student_001"
            },
            "methodology": {},
            "competencies": {
                "raw_occurrences": [],
                "aggregated": [],
                "calibrated": [],
                "esco_interpreted": []
            },
            "semantic_domains": [],
            "occupation_orientation": {},
            "rag": {
                "evidence_chunks": []
            }
        }
    )


@app.get("/api/clusters")
def get_clusters():
    return safe_load_json(
        CLUSTERS_PATH,
        {
            "student_id": "student_001",
            "clusters": []
        }
    )


@app.get("/api/report")
def get_report():
    report_path = OUTPUT_DIR / "employability_report.txt"

    report = safe_load_text(
        report_path,
        "No employability report has been generated yet."
    )

    return {
        "student_id": "student_001",
        "report": report
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Academic Evidence Profiling System is running"
    }


@app.get("/api/occupation-orientation")
def get_occupation_orientation():
    return safe_load_json(
        OCCUPATION_ORIENTATION_PATH,
        {
            "student_id": "student_001",
            "top_occupation_orientations": [],
            "prioritised_occupation_orientations": [],
            "all_occupation_orientations": [],
            "weak_or_possible_noise_signals": []
        }
    )


@app.post("/generate-report")
def generate_report():

    subprocess.run(
        [
            "python",
            "scripts/generate_employability_report.py"
        ],
        cwd=BASE_DIR
    )

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )


@app.post("/generate-targeted-report")
def generate_targeted_report(occupation_uri: str = Form(...)):

    subprocess.run(
        [
            "python",
            "scripts/generate_employability_report.py",
            "--mode",
            "targeted",
            "--occupation-uri",
            occupation_uri
        ],
        cwd=BASE_DIR
    )

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )

@app.get("/student-input")
def student_input_page(request: Request):

    print("SESSION RUNS:", SESSION_RUNS)

    modules_data = load_json_from_path(
        DATA_DIR / "modules.json"
    )

    return templates.TemplateResponse(
        request=request,
        name="student_input.html",
        context={
            "modules": modules_data["modules"],
            "input_error": LAST_INPUT_ERROR
        }
    )

@app.post("/student-input")
async def save_student_input(request: Request):
    global LAST_INPUT_ERROR
    LAST_INPUT_ERROR = None

    form = await request.form()

    student_name = form.get("student_name")

    # Store validated module assessment structures
    selected_modules = []

    module_codes = form.getlist("module_code")

    try:
        for module_code in module_codes:
            final_grade_raw = form.get(f"final_grade_{module_code}")
            coursework_grade_raw = form.get(f"coursework_grade_{module_code}")
            coursework_weight_raw = form.get(f"coursework_weight_{module_code}")
            coursework_components_raw = form.get(f"coursework_components_{module_code}", "1")
            coursework_2_grade_raw = form.get(f"coursework_2_grade_{module_code}")

            if not final_grade_raw or not coursework_grade_raw or not coursework_weight_raw:
                raise ValueError(
                    f"Module {module_code}: final grade, coursework grade and coursework weight are required."
                )

            final_grade = validate_grade(
                final_grade_raw,
                f"{module_code} final grade"
            )

            coursework_grade = validate_grade(
                coursework_grade_raw,
                f"{module_code} coursework grade"
            )

            coursework_weight = validate_weight(
                coursework_weight_raw,
                f"{module_code} coursework weight"
            )

            if coursework_components_raw not in ["1", "2"]:
                raise ValueError(
                    f"{module_code}: coursework components must be either 1 or 2."
                )

            coursework_components = int(coursework_components_raw)

            courseworks = [
                {
                    "component": "coursework_1",
                    "grade": coursework_grade,
                    "weight": coursework_weight
                    if coursework_components == 1
                    else coursework_weight / 2
                }
            ]

            if coursework_components == 2:
                if not coursework_2_grade_raw:
                    raise ValueError(
                        f"{module_code}: coursework 2 grade is required because 2 coursework components were selected."
                    )

                coursework_2_grade = validate_grade(
                    coursework_2_grade_raw,
                    f"{module_code} coursework 2 grade"
                )

                courseworks.append({
                    "component": "coursework_2",
                    "grade": coursework_2_grade,
                    "weight": coursework_weight / 2
                })

            selected_modules.append({
                "module_code": module_code,
                "final_grade": final_grade,
                "coursework_weight": coursework_weight,
                "coursework_components": coursework_components,
                "courseworks": courseworks
            })

    except ValueError as error:
        LAST_INPUT_ERROR = str(error)

        return RedirectResponse(
            url="/student-input",
            status_code=303
        )
    
    if not selected_modules:
        LAST_INPUT_ERROR = (
            "Please select at least one completed module before generating the academic evidence profile."
        )

        return RedirectResponse(
            url="/student-input",
            status_code=303
        )

    student_input = {
        "student_id": "student_001",
        "student_name": student_name,
        "selected_modules": selected_modules
    }

    save_json_to_path(
        student_input,
        STUDENT_INPUT_PATH
    )

    # Execute the academic evidence profiling pipeline after validation
    pipeline_success = run_pipeline_safely()

    if pipeline_success:
        calibrated_profile = safe_load_json(
            PROFILE_PATH,
            {
                "aggregated_skills": []
            }
        )

        clusters_data = safe_load_json(
            CLUSTERS_PATH,
            {
                "clusters": []
            }
        )

        aggregated_skills = calibrated_profile.get(
            "aggregated_skills",
            []
        )

        cluster_items = clusters_data.get(
            "clusters",
            []
        )

        top_skill = (
            aggregated_skills[0].get("display_title", "Unknown")
            if aggregated_skills
            else "No skills extracted"
        )

        domains = []

        for cluster in cluster_items:
            label = cluster.get("cluster_label", "Unknown")

            if label != "General Competency Domain" and label not in domains:
                domains.append(label)

        top_domain = (
            domains[0]
            if domains
            else "No domain generated"
        )

        run_snapshot = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "student_name": student_name,
            "modules": [
                module["module_code"]
                for module in selected_modules
            ],
            "top_skill": top_skill,
            "top_domain": top_domain
        }

        SESSION_RUNS.insert(0, run_snapshot)
        SESSION_RUNS[:] = SESSION_RUNS[:5]

    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )

@app.post("/export-pdf")
def export_pdf():
    global LAST_PIPELINE_ERROR

    pdf_path = OUTPUT_DIR / "academic_evidence_profile_report.pdf"

    try:
        # Generate XAI academic evidence PDF report
        result = subprocess.run(
            [
                "python",
                "scripts/export_pdf_report.py"
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            LAST_PIPELINE_ERROR = (
                "The PDF report could not be exported. "
                "Please close any open PDF file and try again.\n\n"
                f"{result.stderr}"
            )

            print("PDF export failed:")
            print(result.stderr)

            return RedirectResponse(
                url="/dashboard",
                status_code=303
            )

        if not pdf_path.exists():
            LAST_PIPELINE_ERROR = (
                "The PDF export script completed, but the expected PDF file "
                "was not found in the output directory."
            )

            return RedirectResponse(
                url="/dashboard",
                status_code=303
            )

        LAST_PIPELINE_ERROR = None

        return FileResponse(
            path=pdf_path,
            filename="academic_evidence_profile_report.pdf",
            media_type="application/pdf"
        )

    except Exception as error:
        LAST_PIPELINE_ERROR = (
            "An unexpected error occurred during PDF export.\n\n"
            f"{str(error)}"
        )

        print("Unexpected PDF export error:")
        print(error)

        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )
