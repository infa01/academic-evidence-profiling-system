import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "output" / "student_occupation_orientation.json"
OCCUPATION_CHART_LIMIT = 12

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "charts" /
    "occupation_orientation_bar_chart.png"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("Loading ESCO occupation-orientation signals...")

    data = load_json(INPUT_PATH)
    occupations = data.get("top_occupation_orientations", [])[
        :OCCUPATION_CHART_LIMIT
    ]

    if not occupations:
        print("No occupation signals available. Skipping occupation chart generation.")
        return

    labels = [
        occupation.get("occupation_label", "Unknown occupation")
        for occupation in occupations
    ][::-1]

    scores = [
        occupation.get("evidence_score", 0)
        for occupation in occupations
    ][::-1]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 7))
    plt.barh(labels, scores)

    plt.xlabel("ESCO Occupation-Orientation Evidence Score")
    plt.ylabel("ESCO Occupation")
    plt.title("Top 12 ESCO Occupation-Orientation Signals")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300)

    print("Occupation orientation chart generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
