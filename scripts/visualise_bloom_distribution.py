import json
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "charts" /
    "bloom_distribution_chart_with_ambiguity.png"
)


BLOOM_ORDER = [
    "Remember",
    "Understand",
    "Apply",
    "Analyse",
    "Evaluate",
    "Create",
    "Mixed/Ambiguous",
    "Unclassified"
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("Loading student skill profile...")

    data = load_json(INPUT_PATH)

    competencies = data.get("competencies", [])

    if not competencies:
        print("No competencies available. Skipping Bloom distribution chart generation.")
        return

    level_counts = defaultdict(lambda: defaultdict(int))

    for competency in competencies:
        cognitive_level = competency.get(
            "cognitive_level",
            "Unclassified"
        )

        module_code = competency.get("module_code", "")
        module_level = module_code[2] if len(module_code) >= 3 else "Unknown"

        level_counts[module_level][cognitive_level] += 1

    module_levels = [
        level
        for level in ["4", "5", "6", "Unknown"]
        if level in level_counts
    ]

    bottom = [0] * len(module_levels)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))

    for bloom_level in BLOOM_ORDER:
        values = [
            level_counts[module_level].get(bloom_level, 0)
            for module_level in module_levels
        ]

        plt.bar(
            module_levels,
            values,
            bottom=bottom,
            label=bloom_level
        )

        bottom = [
            bottom[index] + values[index]
            for index in range(len(values))
        ]

    plt.xlabel("Academic Module Level")
    plt.ylabel("Number of Extracted Competencies")
    plt.title("Bloom Cognitive Depth by Academic Module Level")
    plt.legend(title="Bloom Level", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=300)

    print("Bloom distribution chart generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
