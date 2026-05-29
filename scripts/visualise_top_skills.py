import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_calibrated.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "charts" /
    "top_skills_bar_chart.png"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("Loading calibrated academic evidence profile...")

    data = load_json(INPUT_PATH)

    skills = data["aggregated_skills"]

    if not skills:
        print("No skills available. Skipping top skills chart generation.")
        return

    top_skills = skills[:10]

    labels = [
        skill.get("display_title", skill.get("skill_name", "Unknown Skill"))
        for skill in top_skills
    ]

    scores = [
        skill.get("aggregated_score", 0)
        for skill in top_skills
    ]

    labels = labels[::-1]
    scores = scores[::-1]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 7))

    plt.barh(labels, scores)

    plt.xlabel("Academic Evidence Strength Score")
    plt.ylabel("ESCO Skill")
    plt.title("Top Academic Evidence Signals Based on ESCO Skill Mapping")

    plt.xlim(0, 1)

    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=300)

    print("Top skills bar chart generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
