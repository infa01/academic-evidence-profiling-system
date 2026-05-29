import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "output" / "student_skill_clusters.json"

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "charts" /
    "domain_strength_bar_chart.png"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_domain_score(skills):
    if not skills:
        return 0

    return sum(
        skill.get("academic_normalized_score", skill.get("aggregated_score", 0))
        for skill in skills
    ) / len(skills)


def main():
    print("Loading semantic competency domains...")

    data = load_json(INPUT_PATH)
    clusters = data.get("clusters", [])

    if not clusters:
        print("No domains available. Skipping domain strength chart generation.")
        return

    domains = []

    for cluster in clusters:
        skills = cluster.get("skills", [])

        if not skills:
            continue

        domains.append({
            "label": cluster.get("cluster_label", "Unknown Domain"),
            "score": round(calculate_domain_score(skills), 4),
            "skill_count": len(skills)
        })

    domains.sort(key=lambda domain: domain["score"], reverse=True)

    labels = [
        f"{domain['label']} ({domain['skill_count']} skills)"
        for domain in domains
    ][::-1]

    scores = [
        domain["score"]
        for domain in domains
    ][::-1]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 7))
    plt.barh(labels, scores)

    plt.xlabel("Average Academic Normalized Evidence Score")
    plt.ylabel("Semantic Competency Domain")
    plt.title("Semantic Domain Strength Based on Academic Evidence")
    plt.xlim(0, 1)

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=300)

    print("Domain strength chart generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
