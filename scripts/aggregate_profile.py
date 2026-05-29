"""
aggregate_profile.py

Aggregates raw competency evidence into consolidated ESCO-aligned
academic competency profiles.

This stage combines:
- semantic similarity,
- Bloom cognitive weighting,
- module level weighting,
- and academic performance evidence

to produce calibrated weighted competency scores with explainable
AI (XAI) scoring components.
"""
import json
from pathlib import Path
from collections import defaultdict

from methodology_config import (
    BLOOM_WEIGHTS,
    get_module_level_weight,
    interpret_raw_evidence
)


# =========================================================
# Core Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "output" / "student_skill_profile.json"
OUTPUT_PATH = BASE_DIR / "output" / "student_skill_profile_aggregated.json"


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
# Weighted Competency Scoring
# =========================================================
def calculate_weighted_score(entry):
    competency_score = entry["competency_score"]
    similarity_score = entry["similarity_score"]
    cognitive_level = entry["cognitive_level"]

    bloom_weight = BLOOM_WEIGHTS.get(cognitive_level, 0.55)

    module_code = entry["module_code"]

    module_weight = get_module_level_weight(module_code)

    # Composite academic competency scoring formula
    weighted_score = (
        competency_score *
        similarity_score *
        bloom_weight *
        module_weight
    )

    # Return weighted score together with XAI traceability components
    return {
        "weighted_score": round(weighted_score, 4),
        "bloom_weight": bloom_weight,
        "module_level_weight": module_weight,
        "grade_weight": competency_score,
        "similarity_score": similarity_score,
        "formula": (
            f"{competency_score} x "
            f"{similarity_score} x "
            f"{bloom_weight} x "
            f"{module_weight}"
        )
    }

# =========================================================
# Aggregated Competency Profile Generation
# =========================================================
def main():
    print("Loading student competency profile...")

    data = load_json(INPUT_PATH)

    # Group competency evidence by ESCO skill URI
    grouped_skills = defaultdict(list)

    for entry in data["competencies"]:
        esco_uri = entry["esco_uri"]
        
        grouped_skills[esco_uri].append(entry)

    aggregated_skills = []

    for esco_uri, entries in grouped_skills.items():
        skill_name = entries[0]["skill_name"]

        # Calculate explainable weighted competency evidence
        weighted_results = [
            calculate_weighted_score(entry)
            for entry in entries
        ]

        weighted_scores = [
            result["weighted_score"]
            for result in weighted_results
        ]

        average_score = sum(weighted_scores) / len(weighted_scores)

        competency_level = interpret_raw_evidence(average_score)

        modules = sorted({
            entry["module_code"]
            for entry in entries
        })

        cognitive_levels = sorted({
            entry["cognitive_level"]
            for entry in entries
        })

        bloom_methods = sorted({
            entry.get("bloom_method", "Unknown")
            for entry in entries
        })

        bloom_confidence_statuses = sorted({
            entry.get("bloom_confidence_status", "-")
            for entry in entries
        })

        bloom_reliability_counts = {}
        bloom_ambiguity_counts = {}

        for entry in entries:
            reliability = entry.get("bloom_classification_reliability", "-")
            ambiguity = entry.get("bloom_ambiguity_status", "-")

            bloom_reliability_counts[reliability] = (
                bloom_reliability_counts.get(reliability, 0) + 1
            )
            bloom_ambiguity_counts[ambiguity] = (
                bloom_ambiguity_counts.get(ambiguity, 0) + 1
            )

        semantic_match_quality_counts = {}
        for entry in entries:
            quality = entry.get("semantic_match_quality", "unknown")
            semantic_match_quality_counts[quality] = (
                semantic_match_quality_counts.get(quality, 0) + 1
            )

        similarity_scores = [
            entry.get("similarity_score", 0)
            for entry in entries
        ]

        # Store aggregated competency profile with XAI metadata
        aggregated_skills.append({
            "esco_uri": esco_uri,
            "skill_name": skill_name,
            "aggregated_score": round(average_score, 4),
            "competency_level": competency_level,
            "occurrences": len(entries),
            "modules": modules,
            "cognitive_levels": cognitive_levels,
            "bloom_reliability_counts": bloom_reliability_counts,
            "bloom_ambiguity_counts": bloom_ambiguity_counts,
            "average_similarity_score": round(
                sum(similarity_scores) / len(similarity_scores),
                4
            ),
            "max_similarity_score": round(max(similarity_scores), 4),
            "semantic_match_quality_counts": semantic_match_quality_counts,
            "bloom_methods": bloom_methods,
            "bloom_confidence_statuses": bloom_confidence_statuses,
            "xai_components": weighted_results
        })

    aggregated_skills.sort(
        key=lambda skill: skill["aggregated_score"],
        reverse=True
    )

    output = {
        "student_id": data["student_id"],
        "aggregated_skills": aggregated_skills
    }

    save_json(output, OUTPUT_PATH)

    print("Aggregated profile generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")

    print("\n--- Top Skills ---")
    for skill in aggregated_skills[:10]:
        print(
            f"{skill['aggregated_score']} | "
            f"{skill['skill_name'][:90]}..."
        )


if __name__ == "__main__":
    main()
