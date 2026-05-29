"""
student_profile.py

Generates the initial student competency profile by combining:
- selected academic modules,
- ESCO-aligned skills,
- Bloom cognitive levels,
- semantic similarity,
- and academic assessment evidence.

This stage produces raw competency evidence before aggregation
and calibration.
"""
import json
from pathlib import Path

# =========================================================
# Core Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

MODULES_PATH = (
    BASE_DIR /
    "output" /
    "modules_with_bloom_esco_filtered.json"
)

STUDENT_INPUT_PATH = (
    BASE_DIR /
    "data" /
    "student_input.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile.json"
)

# =========================================================
# Utility Functions
# =========================================================
def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

# =========================================================
# Academic Performance Calculations
# =========================================================

# Estimate exam contribution based on coursework structure
def calculate_exam_grade(
    final_module_grade,
    coursework_grade,
    coursework_weight
):
    exam_weight = 1 - coursework_weight

    if exam_weight <= 0:
        return final_module_grade, 0

    exam_grade = (
        final_module_grade -
        (coursework_grade * coursework_weight)
    ) / exam_weight

    return round(exam_grade, 2), round(exam_weight, 2)

# =========================================================
# Student Competency Profile Generation
# =========================================================

# Convert academic performance into normalized competency evidence
def calculate_competency_score(
    final_module_grade
):
    return round(final_module_grade / 100, 4)

def main():

    print("Loading datasets...")

    modules_data = load_json(MODULES_PATH)

    student_input = load_json(STUDENT_INPUT_PATH)

    profile = {
        "student_id": student_input["student_id"],
        "competencies": []
    }

    # Create fast module lookup by module code
    modules_lookup = {
        module["module_code"]: module
        for module in modules_data["modules"]
    }

    print("Generating competency profile...\n")

    # Generate competency evidence for each selected academic module
    for selected_module in student_input["selected_modules"]:

        module_code = selected_module["module_code"]

        if module_code not in modules_lookup:
            print(f"Module not found: {module_code}")
            continue

        module = modules_lookup[module_code]

        final_module_grade = selected_module[
            "final_grade"
        ]

        coursework_weight = selected_module[
            "coursework_weight"
        ]

        courseworks = selected_module["courseworks"]

        coursework_grade = sum(
            cw["grade"] * cw["weight"]
            for cw in courseworks
        ) / coursework_weight

        exam_grade, exam_weight = calculate_exam_grade(
            final_module_grade,
            coursework_grade,
            coursework_weight
        )

        competency_score = calculate_competency_score(
            final_module_grade
        )

        print(
            f"{module_code} | "
            f"Final: {final_module_grade} | "
            f"CW: {coursework_grade} | "
            f"Exam: {exam_grade}"
        )

        # Process learning outcomes and ESCO-aligned skills
        for lo in module["learning_outcomes"]:

            bloom = lo.get("bloom", {})
            esco = lo.get("esco", {})

            skills = esco.get("skills", [])

            for skill in skills:

                competency_entry = {
                    "module_code": module_code,
                    "learning_outcome_id": lo["lo_id"],
                    
                    "esco_uri": skill["uri"],
                    "skill_name": skill["name"],

                    "similarity_score": skill.get("similarity_score", 0),
                    "semantic_match_quality": skill.get(
                        "semantic_match_quality",
                        "unknown"
                    ),
                    "semantic_match_note": skill.get(
                        "semantic_match_note",
                        "-"
                    ),
                    "candidate_rank_by_similarity": skill.get(
                        "candidate_rank_by_similarity",
                        "-"
                    ),

                    "cognitive_level": bloom.get("cognitive_level", "Unknown"),

                    "bloom_method": bloom.get("method", "Unknown"),
                    "bloom_rule": bloom.get("rule", "Unknown"),
                    "primary_action_verb": bloom.get("primary_action_verb"),
                    "bloom_confidence": bloom.get("bloom_confidence", "-"),
                    "bloom_confidence_status": bloom.get("confidence_status", "-"),
                    "bloom_score_margin": bloom.get("score_margin", "-"),
                    "bloom_is_near_tie": bloom.get("is_near_tie", False),
                    "bloom_near_tie_margin_threshold": bloom.get(
                        "near_tie_margin_threshold",
                        "-"
                    ),
                    "second_bloom_candidate": bloom.get(
                        "second_bloom_candidate",
                        {}
                    ),
                    "bloom_classification_reliability": bloom.get(
                        "classification_reliability",
                        "-"
                    ),
                    "bloom_ambiguity_status": bloom.get("ambiguity_status", "-"),
                    "bloom_evidence_role": bloom.get("bloom_evidence_role", "-"),
                    "candidate_levels_from_verbs": bloom.get("candidate_levels_from_verbs", []),
                    "top_bloom_candidates": bloom.get("top_bloom_candidates", []),
                    "multi_label_bloom_evidence": bloom.get(
                        "multi_label_bloom_evidence",
                        {}
                    ),

                    "final_module_grade": final_module_grade,

                    "estimated_exam_grade": exam_grade,

                    "coursework_grade": coursework_grade,

                    "competency_score": competency_score
                }

                profile["competencies"].append(competency_entry)

    save_json(profile, OUTPUT_PATH)

    print("\nStudent profile generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")

if __name__ == "__main__":
    main()
