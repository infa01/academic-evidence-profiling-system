"""
calibrate_scores.py

Applies academic competency calibration and normalization to the
aggregated competency profile.

This stage introduces:
- academic competency ceiling normalization,
- relative within-profile ranking,
- evidence interpretation levels,
- and calibration metadata for explainable AI reporting.

"""
import json
from pathlib import Path

from methodology_config import (
    ACADEMIC_EVIDENCE_CEILING,
    interpret_academic_evidence,
    methodology_snapshot
)


# =========================================================
# Core Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_aggregated_enriched.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_calibrated.json"
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
# Academic Competency Calibration
# =========================================================
def main():
    print("Loading enriched skill profile...")

    data = load_json(INPUT_PATH)
    skills = data["aggregated_skills"]

    if not skills:
        data["calibration"] = {
            "method": "academic ceiling normalization + relative profile ranking",
            "academic_evidence_ceiling": round(ACADEMIC_EVIDENCE_CEILING, 4),
            "note": "No skills were available for calibration."
        }

        save_json(data, OUTPUT_PATH)
        return

    # Collect raw aggregated competency scores
    raw_scores = [
        skill["aggregated_score"]
        for skill in skills
    ]

    min_score = min(raw_scores)
    max_score = max(raw_scores)

    print(f"Min raw score: {min_score}")
    print(f"Max raw score: {max_score}")

    for skill in skills:
        raw_score = skill["aggregated_score"]

        # Normalize against theoretical academic competency ceiling
        academic_normalized_score = raw_score / ACADEMIC_EVIDENCE_CEILING
        academic_normalized_score = min(academic_normalized_score, 1.0)

        # Calculate within-profile relative competency ranking
        if max_score == min_score:
            relative_rank_score = 1.0
        else:
            relative_rank_score = (
                raw_score - min_score
            ) / (
                max_score - min_score
            )

        academic_normalized_score = round(academic_normalized_score, 4)
        relative_rank_score = round(relative_rank_score, 4)

        skill["raw_score"] = raw_score

        skill["academic_normalized_score"] = academic_normalized_score
        skill["academic_normalized_percentage"] = round(
            academic_normalized_score * 100,
            2
        )

        skill["relative_rank_score"] = relative_rank_score
        skill["relative_rank_percentage"] = round(
            relative_rank_score * 100,
            2
        )

        # Backwards compatibility for dashboard and charts
        skill["normalized_score"] = academic_normalized_score
        skill["normalized_percentage"] = round(
            academic_normalized_score * 100,
            2
        )

        skill["interpreted_level"] = interpret_academic_evidence(
            academic_normalized_score
        )

    # Store calibration metadata for XAI transparency and PDF reporting
    data["calibration"] = {
        "method": "academic ceiling normalization + relative profile ranking",
        "academic_evidence_ceiling": round(ACADEMIC_EVIDENCE_CEILING, 4),
        "academic_competency_ceiling": round(ACADEMIC_EVIDENCE_CEILING, 4),
        "academic_ceiling_formula": (
            "1.00 grade weight x 1.00 semantic similarity max x "
            "0.85 Bloom max x 1.10 Level 6 module weight = 0.935"
        ),
        "min_raw_score": min_score,
        "max_raw_score": max_score,
        "academic_normalization_note": (
            "Academic normalized scores are calculated against the theoretical "
            "academic evidence ceiling of the scoring model."
        ),
        "relative_rank_note": (
            "Relative profile rank is calculated using min-max normalization "
            "within the current student's extracted competency profile and is "
            "provided only for within-profile comparison."
        ),
        "methodology": methodology_snapshot()
    }

    save_json(data, OUTPUT_PATH)

    print("Calibration completed.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
