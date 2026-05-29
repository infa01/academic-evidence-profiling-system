import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "output" / "student_skill_clusters.json"

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "charts" /
    "clustered_domain_heatmap.png"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_domain_module_score(skills, module):
    module_scores = []

    for skill in skills:
        if module in skill.get("modules", []):
            module_scores.append(skill.get("aggregated_score", 0))

    if not module_scores:
        return 0

    return sum(module_scores) / len(module_scores)


def main():
    print("Loading student skill clusters...")

    data = load_json(INPUT_PATH)

    clusters = data.get("clusters", [])

    if not clusters:
        print("No clusters available. Skipping clustered domain heatmap generation.")
        return

    modules = sorted({
        module
        for cluster in clusters
        for skill in cluster.get("skills", [])
        for module in skill.get("modules", [])
    })

    if not modules:
        print("No modules available. Skipping clustered domain heatmap generation.")
        return

    domain_labels = [
        cluster.get("cluster_label", "Unknown Domain")
        for cluster in clusters
    ]

    matrix = []

    for module in modules:
        row = []

        for cluster in clusters:
            score = calculate_domain_module_score(
                cluster["skills"],
                module
            )

            row.append(score)

        matrix.append(row)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))

    plt.imshow(matrix, aspect="auto")

    plt.xticks(
        range(len(domain_labels)),
        domain_labels,
        rotation=30,
        ha="right"
    )

    plt.yticks(
        range(len(modules)),
        modules
    )

    plt.xlabel("Competency Domain")
    plt.ylabel("Module")
    plt.title("Clustered Competency Domain Heatmap by Module")

    plt.colorbar(label="Average Domain Competency Score")

    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=300)

    print("Clustered domain heatmap generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()