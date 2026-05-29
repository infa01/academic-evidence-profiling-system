"""
Builds the canonical structured student evidence profile.

Intermediate JSON files remain useful for debugging and dissertation
traceability, but this file creates the final contract that downstream
dashboard, RAG, LLM and PDF stages should gradually converge on.
"""

import json
from pathlib import Path

from methodology_config import methodology_snapshot


BASE_DIR = Path(__file__).resolve().parent.parent

STUDENT_INPUT_PATH = BASE_DIR / "data" / "student_input.json"
MODULES_WITH_EVIDENCE_PATH = BASE_DIR / "output" / "modules_with_bloom_esco_filtered.json"
RAW_PROFILE_PATH = BASE_DIR / "output" / "student_skill_profile.json"
CALIBRATED_PROFILE_PATH = BASE_DIR / "output" / "student_skill_profile_calibrated.json"
ESCO_INTERPRETED_PROFILE_PATH = BASE_DIR / "output" / "student_skill_profile_esco_interpreted.json"
CLUSTERS_PATH = BASE_DIR / "output" / "student_skill_clusters.json"
OCCUPATION_ORIENTATION_PATH = BASE_DIR / "output" / "student_occupation_orientation.json"

OUTPUT_PATH = BASE_DIR / "output" / "final_student_competency_profile.json"


def load_json(path, fallback):
    if not path.exists():
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def build_input_summary(student_input):
    selected_modules = student_input.get("selected_modules", [])

    return {
        "selected_module_count": len(selected_modules),
        "selected_modules": [
            {
                "module_code": module.get("module_code"),
                "final_grade": module.get("final_grade"),
                "coursework_weight": module.get("coursework_weight"),
                "coursework_components": module.get("coursework_components"),
                "courseworks": module.get("courseworks", [])
            }
            for module in selected_modules
        ]
    }


def build_learning_outcome_evidence(modules_data):
    evidence = []

    for module in modules_data.get("modules", []):
        module_code = module.get("module_code")
        module_title = module.get("module_title", module.get("title", ""))
        module_level = module.get("module_level", module.get("level"))

        for learning_outcome in module.get("learning_outcomes", []):
            bloom = learning_outcome.get("bloom", {})
            esco = learning_outcome.get("esco", {})

            evidence.append({
                "module_code": module_code,
                "module_title": module_title,
                "module_level": module_level,
                "learning_outcome_id": learning_outcome.get("lo_id"),
                "learning_outcome_text": learning_outcome.get("text"),
                "bloom_evidence": {
                    "cognitive_level": bloom.get("cognitive_level", "Unknown"),
                    "method": bloom.get("method", "Unknown"),
                    "rule": bloom.get("rule", "Unknown"),
                    "primary_action_verb": bloom.get("primary_action_verb"),
                    "matched_verbs": bloom.get("matched_verbs", []),
                    "confidence": bloom.get("bloom_confidence"),
                    "confidence_status": bloom.get("confidence_status"),
                    "classification_reliability": bloom.get(
                        "classification_reliability"
                    ),
                    "classification_reliability_note": bloom.get(
                        "classification_reliability_note"
                    ),
                    "ambiguity_status": bloom.get("ambiguity_status"),
                    "evidence_role": bloom.get("bloom_evidence_role"),
                    "score_margin": bloom.get("score_margin"),
                    "top_candidates": bloom.get("top_bloom_candidates", []),
                    "multi_label_bloom_evidence": bloom.get(
                        "multi_label_bloom_evidence",
                        {}
                    ),
                    "interpretation_note": bloom.get("interpretation_note")
                },
                "esco_skill_evidence": [
                    {
                        "esco_uri": skill.get("uri"),
                        "skill_name": skill.get("name"),
                        "preferred_label": skill.get("preferred_label"),
                        "display_title": skill.get("display_title"),
                        "similarity_score": skill.get("similarity_score"),
                        "semantic_match_quality": skill.get(
                            "semantic_match_quality"
                        ),
                        "semantic_match_note": skill.get("semantic_match_note"),
                        "candidate_rank_by_similarity": skill.get(
                            "candidate_rank_by_similarity"
                        )
                    }
                    for skill in esco.get("skills", [])
                ],
                "similarity_threshold": esco.get("similarity_threshold"),
                "evaluated_skill_count": esco.get("evaluated_skill_count", 0),
                "rejected_below_threshold_count": esco.get(
                    "rejected_below_threshold_count",
                    0
                ),
                "match_quality_counts": esco.get("match_quality_counts", {}),
                "retained_esco_skill_count": esco.get("number_of_skills", 0)
            })

    return evidence


def build_module_evidence(learning_outcome_evidence):
    modules = {}

    for item in learning_outcome_evidence:
        module_code = item.get("module_code")

        if module_code not in modules:
            modules[module_code] = {
                "module_code": module_code,
                "module_title": item.get("module_title"),
                "module_level": item.get("module_level"),
                "learning_outcome_count": 0,
                "retained_esco_skill_count": 0,
                "bloom_levels": {}
            }

        modules[module_code]["learning_outcome_count"] += 1
        modules[module_code]["retained_esco_skill_count"] += item.get(
            "retained_esco_skill_count",
            0
        )

        bloom_level = item.get("bloom_evidence", {}).get(
            "cognitive_level",
            "Unknown"
        )

        modules[module_code]["bloom_levels"][bloom_level] = (
            modules[module_code]["bloom_levels"].get(bloom_level, 0) + 1
        )

    return list(modules.values())


def build_rag_chunk(chunk_id, chunk_type, title, text, source, priority_score=0):
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "title": title,
        "text": text,
        "source": source,
        "priority_score": round(float(priority_score or 0), 4)
    }


def build_rag_chunks(profile, clusters, occupation_orientation):
    chunks = []

    for index, skill in enumerate(profile.get("aggregated_skills", [])[:20], start=1):
        title = skill.get("display_title", skill.get("skill_name", "Unknown Skill"))
        modules = ", ".join(skill.get("modules", []))
        levels = ", ".join(skill.get("cognitive_levels", []))

        text = (
            f"{title} has academic evidence score {skill.get('aggregated_score')} "
            f"and academic normalized evidence {skill.get('academic_normalized_percentage')}%. "
            f"Evidence level: {skill.get('interpreted_level')}. "
            f"Contributing modules: {modules}. Bloom levels: {levels}. "
            "Interpret this as academic evidence strength, not professional certification."
        )

        chunks.append(build_rag_chunk(
            chunk_id=f"skill_{index}",
            chunk_type="competency_evidence",
            title=title,
            text=text,
            source={
                "json_path": "competencies.calibrated",
                "esco_uri": skill.get("esco_uri")
            },
            priority_score=skill.get("academic_normalized_score", 0)
        ))

    for index, cluster in enumerate(clusters.get("clusters", []), start=1):
        label = cluster.get("cluster_label", "Unknown Domain")
        skills = cluster.get("skills", [])
        skill_titles = [
            skill.get("display_title", "Unknown Skill")
            for skill in skills[:8]
        ]

        average_score = 0
        if skills:
            average_score = sum(
                skill.get("academic_normalized_score", 0)
                for skill in skills
            ) / len(skills)

        text = (
            f"{label} is a semantic competency domain containing: "
            f"{', '.join(skill_titles)}. "
            "The domain was produced through semantic clustering of ESCO-aligned skills."
        )

        chunks.append(build_rag_chunk(
            chunk_id=f"domain_{index}",
            chunk_type="semantic_domain",
            title=label,
            text=text,
            source={"json_path": "semantic_domains"},
            priority_score=average_score
        ))

    for index, occupation in enumerate(
        occupation_orientation.get("top_occupation_orientations", [])[:15],
        start=1
    ):
        label = occupation.get("occupation_label", "Unknown occupation")

        text = (
            f"{label} appears as an ESCO occupation-orientation signal with "
            f"evidence score {occupation.get('evidence_score')}. "
            f"Signal level: {occupation.get('signal_level')}. "
            f"Matched skills: {occupation.get('matched_skill_count')}. "
            "This should be described as career orientation, not as an automated job recommendation."
        )

        chunks.append(build_rag_chunk(
            chunk_id=f"occupation_{index}",
            chunk_type="occupation_orientation",
            title=label,
            text=text,
            source={
                "json_path": "occupation_orientation.top_occupation_orientations",
                "occupation_uri": occupation.get("occupation_uri")
            },
            priority_score=occupation.get("evidence_score", 0)
        ))

    for key, note in methodology_snapshot().get("notes", {}).items():
        chunks.append(build_rag_chunk(
            chunk_id=f"methodology_{key}",
            chunk_type="methodology_note",
            title=key.replace("_", " ").title(),
            text=note,
            source={"json_path": "methodology.notes"},
            priority_score=1
        ))

    chunks.sort(
        key=lambda chunk: (
            chunk["priority_score"],
            chunk["chunk_type"]
        ),
        reverse=True
    )

    return chunks


def main():
    print("Building final structured competency profile...")

    student_input = load_json(STUDENT_INPUT_PATH, {})
    modules_data = load_json(MODULES_WITH_EVIDENCE_PATH, {"modules": []})
    raw_profile = load_json(RAW_PROFILE_PATH, {"competencies": []})
    calibrated_profile = load_json(CALIBRATED_PROFILE_PATH, {"aggregated_skills": []})
    esco_interpreted_profile = load_json(
        ESCO_INTERPRETED_PROFILE_PATH,
        calibrated_profile
    )
    clusters = load_json(CLUSTERS_PATH, {"clusters": []})
    occupation_orientation = load_json(
        OCCUPATION_ORIENTATION_PATH,
        {
            "top_occupation_orientations": [],
            "prioritised_occupation_orientations": [],
            "weak_or_possible_noise_signals": [],
            "all_occupation_orientations": []
        }
    )

    learning_outcome_evidence = build_learning_outcome_evidence(modules_data)
    module_evidence = build_module_evidence(learning_outcome_evidence)

    final_profile = {
        "metadata": {
            "profile_schema_version": "1.0",
            "profile_type": "explainable_academic_evidence_profile",
            "generated_by": "scripts/build_final_profile.py"
        },
        "student": {
            "student_id": student_input.get("student_id", "student_001"),
            "student_name": student_input.get("student_name")
        },
        "methodology": methodology_snapshot(),
        "input_summary": build_input_summary(student_input),
        "module_evidence": module_evidence,
        "learning_outcome_evidence": learning_outcome_evidence,
        "competencies": {
            "raw_occurrences": raw_profile.get("competencies", []),
            "aggregated": calibrated_profile.get("aggregated_skills", []),
            "calibrated": calibrated_profile.get("aggregated_skills", []),
            "esco_interpreted": esco_interpreted_profile.get("aggregated_skills", [])
        },
        "semantic_domains": clusters.get("clusters", []),
        "occupation_orientation": occupation_orientation,
        "xai": {
            "calibration": calibrated_profile.get("calibration", {}),
            "esco_interpretation_summary": esco_interpreted_profile.get(
                "esco_interpretation_summary",
                {}
            ),
            "score_interpretation": (
                "The score is an academic evidence-strength ranking used to support "
                "XAI interpretation and RAG retrieval. It should not be interpreted "
                "as a direct measurement of professional competence."
            )
        },
        "rag": {
            "retrieval_strategy": (
                "Retrieve structured evidence chunks by report section and priority "
                "score, then use the retrieved evidence to ground LLM generation."
            ),
            "evidence_chunks": build_rag_chunks(
                calibrated_profile,
                clusters,
                occupation_orientation
            )
        },
        "visual_analytics": {
            "generated_files": [
                "output/charts/top_skills_bar_chart.png",
                "output/charts/bloom_distribution_chart.png",
                "output/charts/domain_strength_bar_chart.png",
                "output/charts/occupation_orientation_bar_chart.png",
                "output/charts/clustered_domain_heatmap.png"
            ],
            "recommended_interpretation": (
                "Charts should communicate evidence strength, Bloom depth, semantic "
                "domains and module-to-domain contribution, not professional mastery."
            )
        }
    }

    save_json(final_profile, OUTPUT_PATH)

    print("Final structured profile generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
