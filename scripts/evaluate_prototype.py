"""
evaluate_prototype.py

Generates a technical evaluation report for the thesis prototype.

The report is intentionally framed as prototype evaluation rather than external
validation. It measures reproducibility-relevant artifacts, evidence quality
signals, scoring sensitivity and RAG traceability from generated pipeline
outputs.
"""

import json
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CALIBRATED_PROFILE_PATH = OUTPUT_DIR / "student_skill_profile_calibrated.json"
RAW_PROFILE_PATH = OUTPUT_DIR / "student_skill_profile.json"
FINAL_PROFILE_PATH = OUTPUT_DIR / "final_student_competency_profile.json"
OCCUPATION_ORIENTATION_PATH = OUTPUT_DIR / "student_occupation_orientation.json"
RAG_METADATA_PATH = OUTPUT_DIR / "rag_generation_metadata.json"
TARGETED_RAG_METADATA_PATH = OUTPUT_DIR / "targeted_rag_generation_metadata.json"
RAG_EVIDENCE_PATH = OUTPUT_DIR / "rag_retrieved_evidence.json"
TARGETED_RAG_EVIDENCE_PATH = OUTPUT_DIR / "targeted_rag_retrieved_evidence.json"
RAG_EVALUATION_PATH = OUTPUT_DIR / "rag_evaluation_metrics.json"

JSON_REPORT_PATH = OUTPUT_DIR / "prototype_evaluation_report.json"
MARKDOWN_REPORT_PATH = OUTPUT_DIR / "prototype_evaluation_report.md"


EXPECTED_CHARTS = [
    "top_skills_bar_chart.png",
    "bloom_distribution_chart.png",
    "domain_strength_bar_chart.png",
    "occupation_orientation_bar_chart.png",
    "clustered_domain_heatmap.png",
]


EXPECTED_ARTIFACTS = [
    "modules_with_bloom_esco_filtered.json",
    "student_skill_profile.json",
    "student_skill_profile_aggregated.json",
    "student_skill_profile_calibrated.json",
    "student_skill_profile_esco_interpreted.json",
    "student_skill_clusters.json",
    "student_occupation_orientation.json",
    "final_student_competency_profile.json",
    "rag_retrieved_evidence.json",
    "rag_generation_metadata.json",
    "rag_evaluation_metrics.json",
]


FORBIDDEN_CAREER_CLAIMS = [
    "guaranteed employability",
    "job suitability",
    "certified skill",
    "professional competence",
    "hiring decision",
    "is a job recommendation",
    "are job recommendations",
    "recommended job",
    "ats bypass",
]


def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def pct(part, whole):
    if not whole:
        return 0.0
    return round((part / whole) * 100, 2)


def top_skill_ids(skills, score_key, limit=10):
    ranked = sorted(
        skills,
        key=lambda skill: skill.get(score_key, 0),
        reverse=True
    )
    return [skill.get("esco_uri") for skill in ranked[:limit]]


def top_overlap(base_ids, variant_ids):
    base = set(base_ids)
    variant = set(variant_ids)
    return {
        "overlap_count": len(base & variant),
        "overlap_percentage": pct(len(base & variant), len(base_ids)),
        "base_only": [item for item in base_ids if item not in variant],
        "variant_only": [item for item in variant_ids if item not in base],
    }


def recompute_variant_score(skill, variant):
    scores = []

    for component in skill.get("xai_components", []):
        grade = component.get("grade_weight", 0)
        similarity = component.get("similarity_score", 0)
        bloom = component.get("bloom_weight", 1)
        level = component.get("module_level_weight", 1)
        bloom_normalized = min(bloom / 0.85, 1)
        level_normalized = min(level / 1.10, 1)

        if variant == "baseline":
            score = component.get("weighted_score", 0)
        elif variant == "without_bloom_weight":
            score = grade * similarity * level
        elif variant == "without_module_level_weight":
            score = grade * similarity * bloom
        elif variant == "grade_similarity_only":
            score = grade * similarity
        elif variant == "stricter_similarity_threshold_0_55":
            if similarity < 0.55:
                continue
            score = grade * similarity * bloom * level
        elif variant == "linear_combination_similarity_0_4_grade_0_3_bloom_0_2_level_0_1":
            score = (
                (0.4 * similarity)
                + (0.3 * grade)
                + (0.2 * bloom_normalized)
                + (0.1 * level_normalized)
            )
        else:
            score = 0

        scores.append(score)

    if not scores:
        return 0

    return round(sum(scores) / len(scores), 4)


def sensitivity_analysis(skills):
    variants = [
        "baseline",
        "without_bloom_weight",
        "without_module_level_weight",
        "grade_similarity_only",
        "stricter_similarity_threshold_0_55",
        "linear_combination_similarity_0_4_grade_0_3_bloom_0_2_level_0_1",
    ]

    variant_rankings = {}
    variant_scores = {}

    for variant in variants:
        scored = []
        for skill in skills:
            score = recompute_variant_score(skill, variant)
            scored.append({
                "esco_uri": skill.get("esco_uri"),
                "display_title": skill.get(
                    "display_title",
                    skill.get("skill_name", "")
                ),
                "score": score,
            })

        scored.sort(key=lambda item: item["score"], reverse=True)
        variant_scores[variant] = scored[:10]
        variant_rankings[variant] = [item["esco_uri"] for item in scored[:10]]

    base_ids = variant_rankings["baseline"]

    return {
        "top_10_rankings": variant_scores,
        "top_10_stability_against_baseline": {
            variant: top_overlap(base_ids, ids)
            for variant, ids in variant_rankings.items()
            if variant != "baseline"
        },
    }


def evidence_quality(calibrated_profile, raw_profile, occupation_data):
    skills = calibrated_profile.get("aggregated_skills", [])
    competencies = raw_profile.get("competencies", [])

    semantic_counts = Counter()
    bloom_reliability_counts = Counter()
    bloom_ambiguity_counts = Counter()

    for skill in skills:
        semantic_counts.update(skill.get("semantic_match_quality_counts", {}))
        bloom_reliability_counts.update(skill.get("bloom_reliability_counts", {}))
        bloom_ambiguity_counts.update(skill.get("bloom_ambiguity_counts", {}))

    total_semantic = sum(semantic_counts.values())
    total_bloom = sum(bloom_reliability_counts.values())

    occupation_categories = Counter(
        occupation.get("evidence_category", "unknown")
        for occupation in occupation_data.get("all_occupation_orientations", [])
    )

    return {
        "accepted_esco_skill_occurrences": len(competencies),
        "aggregated_skill_count": len(skills),
        "semantic_match_quality_counts": dict(semantic_counts),
        "semantic_match_quality_percentages": {
            key: pct(value, total_semantic)
            for key, value in semantic_counts.items()
        },
        "bloom_reliability_counts": dict(bloom_reliability_counts),
        "bloom_reliability_percentages": {
            key: pct(value, total_bloom)
            for key, value in bloom_reliability_counts.items()
        },
        "bloom_ambiguity_counts": dict(bloom_ambiguity_counts),
        "occupation_signal_counts": {
            "total": occupation_data.get("total_occupations", 0),
            "prioritised": occupation_data.get(
                "prioritised_occupation_count", 0
            ),
            "weak_or_possible_noise": occupation_data.get(
                "weak_or_possible_noise_count", 0
            ),
            "by_category": dict(occupation_categories),
        },
    }


def artifact_coverage():
    artifacts = {}
    for name in EXPECTED_ARTIFACTS:
        path = OUTPUT_DIR / name
        artifacts[name] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    charts = {}
    for name in EXPECTED_CHARTS:
        path = CHARTS_DIR / name
        charts[name] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    return {
        "expected_artifacts": artifacts,
        "expected_charts": charts,
        "artifact_completion_percentage": pct(
            sum(1 for item in artifacts.values() if item["exists"]),
            len(artifacts)
        ),
        "chart_completion_percentage": pct(
            sum(1 for item in charts.values() if item["exists"]),
            len(charts)
        ),
    }


def rag_traceability(metadata_path, evidence_path):
    metadata = load_json(metadata_path, default={})
    evidence = load_json(evidence_path, default={})

    sections = metadata.get("retrieval_summary", {}).get("sections", {})
    quality = metadata.get("quality_checks", {})

    retrieved_chunks = []
    if isinstance(evidence, dict):
        evidence_sections = evidence.get("sections", evidence)
        for section in evidence_sections.values():
            retrieved_chunks.extend(section.get("chunks", []))

    return {
        "metadata_exists": metadata_path.exists(),
        "evidence_exists": evidence_path.exists(),
        "generation_mode": metadata.get("generation_mode"),
        "generation_status": quality.get("generation_status"),
        "section_count": metadata.get(
            "retrieval_summary", {}
        ).get("section_count", 0),
        "total_retrieved_chunks": metadata.get(
            "retrieval_summary", {}
        ).get("total_retrieved_chunks", 0),
        "sections": {
            key: {
                "chunk_count": value.get("chunk_count", 0),
                "average_retrieval_score": value.get(
                    "average_retrieval_score"
                ),
                "min_retrieval_score": value.get("min_retrieval_score"),
                "max_retrieval_score": value.get("max_retrieval_score"),
            }
            for key, value in sections.items()
        },
        "quality_checks": quality,
        "generation_metrics": metadata.get("generation_metrics", {}),
        "model_info": metadata.get("model_info", {}),
        "prompt_character_count": metadata.get("prompt_character_count"),
        "retrieved_chunk_count_from_evidence_file": len(retrieved_chunks),
    }


def dashboard_evidence_coverage(final_profile):
    competencies = final_profile.get("competencies", {})
    calibrated = competencies.get("calibrated")
    aggregated = competencies.get("aggregated")

    has_skill_evidence = bool(calibrated or aggregated)

    checks = {
        "has_methodology_snapshot": bool(final_profile.get("methodology")),
        "has_rag_chunks": bool(
            final_profile.get("rag", {}).get("evidence_chunks")
        ),
        "has_visual_analytics_refs": bool(
            final_profile.get("visual_analytics", {}).get("generated_files")
        ),
        "has_occupation_orientation": bool(
            final_profile.get("occupation_orientation", {}).get(
                "top_occupation_orientations"
            )
        ),
        "has_skill_evidence": has_skill_evidence,
    }

    return {
        "checks": checks,
        "coverage_percentage": pct(
            sum(1 for value in checks.values() if value),
            len(checks)
        ),
    }


def report_text_checks():
    report_paths = [
        OUTPUT_DIR / "employability_report.txt",
        OUTPUT_DIR / "targeted_occupation_report.txt",
    ]

    checks = {}
    for path in report_paths:
        if not path.exists():
            checks[path.name] = {"exists": False}
            continue

        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        found = [
            phrase
            for phrase in FORBIDDEN_CAREER_CLAIMS
            if re.search(rf"\b{re.escape(phrase)}\b", text)
        ]
        checks[path.name] = {
            "exists": True,
            "character_count": len(text),
            "forbidden_claims_found": found,
            "forbidden_claim_check_passed": not found,
        }

    return checks


def rag_generation_evaluation():
    evaluation = load_json(RAG_EVALUATION_PATH, default={})
    if not evaluation:
        return {
            "exists": False,
            "note": (
                "Run scripts/evaluate_rag_generation.py after generic LLM "
                "generation to produce lightweight RAGAS-inspired metrics."
            ),
        }

    return {
        "exists": True,
        "evaluation_type": evaluation.get("evaluation_type"),
        "official_ragas_package_used": evaluation.get(
            "official_ragas_package_used"
        ),
        "context_precision_proxy": evaluation
            .get("context_precision", {})
            .get("overall_context_precision_proxy"),
        "section_relevance_proxy": evaluation
            .get("section_relevance", {})
            .get("overall_section_relevance_proxy"),
        "faithfulness_proxy": evaluation
            .get("faithfulness", {})
            .get("faithfulness_proxy"),
        "answer_relevance_proxy": evaluation
            .get("answer_relevance", {})
            .get("answer_relevance_proxy"),
        "evidence_mention_coverage": evaluation
            .get("evidence_mention_coverage", {})
            .get("evidence_mention_coverage"),
    }


def build_markdown(report):
    lines = [
        "# Prototype Technical Evaluation Report",
        "",
        "This report evaluates the prototype as an explainable academic evidence "
        "profiling system. It is not an external validation of professional "
        "competence or career suitability.",
        "",
        "## Reproducibility Artifacts",
        "",
        f"- Artifact completion: {report['artifact_coverage']['artifact_completion_percentage']}%",
        f"- Chart completion: {report['artifact_coverage']['chart_completion_percentage']}%",
        "",
        "## Evidence Quality Summary",
        "",
        f"- Accepted ESCO skill occurrences: {report['evidence_quality']['accepted_esco_skill_occurrences']}",
        f"- Aggregated ESCO skills: {report['evidence_quality']['aggregated_skill_count']}",
        f"- Semantic match quality: {report['evidence_quality']['semantic_match_quality_counts']}",
        f"- Bloom reliability: {report['evidence_quality']['bloom_reliability_counts']}",
        f"- Bloom ambiguity: {report['evidence_quality']['bloom_ambiguity_counts']}",
        f"- Occupation signals: {report['evidence_quality']['occupation_signal_counts']}",
        "",
        "## Scoring Sensitivity",
        "",
    ]

    stability = report["scoring_sensitivity"]["top_10_stability_against_baseline"]
    for variant, data in stability.items():
        lines.append(
            f"- {variant}: {data['overlap_count']}/10 top skills retained "
            f"({data['overlap_percentage']}%)"
        )

    lines.extend([
        "",
        "## RAG Traceability",
        "",
    ])

    for label, rag in report["rag_traceability"].items():
        lines.extend([
            f"### {label}",
            f"- Metadata exists: {rag['metadata_exists']}",
            f"- Evidence exists: {rag['evidence_exists']}",
            f"- Generation mode: {rag['generation_mode']}",
            f"- Generation status: {rag['generation_status']}",
            f"- Model info: {rag['model_info']}",
            f"- Prompt characters: {rag['prompt_character_count']}",
            f"- Generation metrics: {rag['generation_metrics']}",
            f"- Sections: {rag['section_count']}",
            f"- Retrieved chunks: {rag['total_retrieved_chunks']}",
            "",
        ])

    lines.extend([
        "## Dashboard Evidence Coverage",
        "",
        f"- Coverage: {report['dashboard_evidence_coverage']['coverage_percentage']}%",
        f"- Checks: {report['dashboard_evidence_coverage']['checks']}",
        "",
        "## Report Text Safety Checks",
        "",
        str(report["report_text_checks"]),
        "",
        "## RAG Generation Evaluation",
        "",
    ])

    rag_evaluation = report["rag_generation_evaluation"]
    if rag_evaluation.get("exists"):
        lines.extend([
            f"- Evaluation type: {rag_evaluation['evaluation_type']}",
            f"- Official RAGAS package used: {rag_evaluation['official_ragas_package_used']}",
            f"- Context precision proxy: {rag_evaluation['context_precision_proxy']}",
            f"- Section relevance proxy: {rag_evaluation['section_relevance_proxy']}",
            f"- Faithfulness proxy: {rag_evaluation['faithfulness_proxy']}",
            f"- Answer relevance proxy: {rag_evaluation['answer_relevance_proxy']}",
            f"- Evidence mention coverage: {rag_evaluation['evidence_mention_coverage']}",
            "",
        ])
    else:
        lines.extend([
            f"- {rag_evaluation['note']}",
            "",
        ])

    lines.extend([
        "## Evaluation Interpretation",
        "",
        "These checks support a technical prototype evaluation: the system can be "
        "assessed for reproducible artifacts, evidence traceability, transparent "
        "quality labels, scoring sensitivity and RAG metadata. They do not replace "
        "expert validation or user evaluation, which remain recommended future work.",
        "",
    ])

    return "\n".join(lines)


def main():
    calibrated_profile = load_json(CALIBRATED_PROFILE_PATH, default={})
    raw_profile = load_json(RAW_PROFILE_PATH, default={})
    final_profile = load_json(FINAL_PROFILE_PATH, default={})
    occupation_data = load_json(OCCUPATION_ORIENTATION_PATH, default={})

    skills = calibrated_profile.get("aggregated_skills", [])

    report = {
        "evaluation_type": "technical_prototype_evaluation",
        "scope_note": (
            "This evaluation checks reproducibility, evidence quality, scoring "
            "sensitivity and RAG traceability. It is not expert validation, user "
            "validation, labour-market validation or professional competence "
            "certification."
        ),
        "artifact_coverage": artifact_coverage(),
        "evidence_quality": evidence_quality(
            calibrated_profile,
            raw_profile,
            occupation_data
        ),
        "scoring_sensitivity": sensitivity_analysis(skills),
        "rag_traceability": {
            "generic": rag_traceability(RAG_METADATA_PATH, RAG_EVIDENCE_PATH),
            "targeted": rag_traceability(
                TARGETED_RAG_METADATA_PATH,
                TARGETED_RAG_EVIDENCE_PATH
            ),
        },
        "dashboard_evidence_coverage": dashboard_evidence_coverage(final_profile),
        "report_text_checks": report_text_checks(),
        "rag_generation_evaluation": rag_generation_evaluation(),
    }

    save_json(report, JSON_REPORT_PATH)
    MARKDOWN_REPORT_PATH.write_text(
        build_markdown(report),
        encoding="utf-8"
    )

    print("Prototype evaluation completed.")
    print(f"JSON report: {JSON_REPORT_PATH}")
    print(f"Markdown report: {MARKDOWN_REPORT_PATH}")


if __name__ == "__main__":
    main()
