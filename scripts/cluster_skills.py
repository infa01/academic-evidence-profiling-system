"""
cluster_skills.py

Groups calibrated competencies into semantic competency domains
using sentence embeddings and agglomerative clustering.

This stage:
- generates semantic embeddings,
- clusters related ESCO competencies,
- and produces human-readable competency domains
for explainable analytics and reporting.

"""
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering


# =========================================================
# Core Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_esco_interpreted.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_clusters.json"
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
# Human-Readable Cluster Interpretation
# =========================================================
def generate_cluster_label(skills):
    """
    Generates a deterministic, market-facing label for a semantic skill cluster.

    The method uses keyword scoring instead of returning the first matched rule.
    This avoids cases where a cluster contains both database and AI concepts but
    is labelled only by whichever rule appears first in the code.

    """
    # Combine skill titles for lightweight rule-based domain interpretation
    text = " ".join(
        skill.get("display_title", "")
        + " "
        + skill.get("preferred_label", "")
        for skill in skills
    ).lower()

    label_keywords = {
        "Data and Database Technologies": [
            "database",
            "relational",
            "dbms",
            "data model",
            "data models",
            "data quality",
            "data warehouse",
            "data structure",
            "data structures",
            "physical structure"
        ],

        "Artificial Intelligence and Data Analytics": [
            "artificial intelligence",
            "principles of artificial intelligence",
            "ai",
            "data mining",
            "analysis results",
            "data ethics",
            "data scientist",
            "analytics"
        ],

        "Software Engineering and Development": [
            "software",
            "programming",
            "computer programming",
            "object-oriented",
            "systems development",
            "application development",
            "solution deployment",
            "configuration management",
            "software specifications",
            "assembly",
            "development life-cycle"
        ],

        "Cybersecurity, Networks and Systems": [
            "cyber",
            "security",
            "network",
            "networks",
            "transmission",
            "hardware",
            "ict hardware",
            "ict communications",
            "communications protocol",
            "protocols"
        ],

        "User-Centred Design and Digital Communication": [
            "documentation",
            "user documentation",
            "user-centered",
            "user-centred",
            "multimedia",
            "presentation",
            "presentation software",
            "content",
            "digital communication"
        ],

        "Research, Professional and Analytical Skills": [
            "report",
            "research",
            "prior learning",
            "personal development",
            "legal requirements",
            "recruit",
            "professional",
            "teach",
            "assessment"
        ],

        "Mathematical and Analytical Computing Methods": [
            "mathematical",
            "analytical",
            "calculation",
            "calculations",
            "scrambling",
            "cryptographic",
            "algorithmic",
            "technical problems"
        ]
    }

    label_scores = {
        label: 0.0
        for label in label_keywords
    }

    for skill in skills:
        skill_text = (
            skill.get("display_title", "")
            + " "
            + skill.get("preferred_label", "")
        ).lower()

        skill_score = float(skill.get("aggregated_score", 0.0))

        for label, keywords in label_keywords.items():
            for keyword in keywords:
                if keyword in skill_text:
                    label_scores[label] += skill_score

    sorted_labels = sorted(
        label_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    best_label, best_score = sorted_labels[0]
    second_score = sorted_labels[1][1] if len(sorted_labels) > 1 else 0.0

    if best_score == 0:
        return "Specialised Technical Knowledge"

    # If the cluster is very mixed, use a broader label.
    if len(skills) >= 10 and second_score > 0 and (best_score - second_score) < 0.35:
        return "Core Computing, Data and Systems Technologies"

    return best_label


def summarize_cluster_esco_metadata(skills):
    skill_type_counts = {}
    reuse_level_counts = {}

    transversal_count = 0
    essential_occupation_total = 0
    optional_occupation_total = 0

    for skill in skills:
        skill_type = skill.get("skill_type", "Unknown")
        reuse_level = skill.get("reuse_level", "Unknown")

        skill_type_counts[skill_type] = skill_type_counts.get(skill_type, 0) + 1
        reuse_level_counts[reuse_level] = reuse_level_counts.get(reuse_level, 0) + 1

        if skill.get("is_transversal", False):
            transversal_count += 1

        essential_occupation_total += skill.get("essential_occupation_count", 0)
        optional_occupation_total += skill.get("optional_occupation_count", 0)

    return {
        "skill_type_distribution": skill_type_counts,
        "reuse_level_distribution": reuse_level_counts,
        "transversal_skill_count": transversal_count,
        "essential_occupation_relation_count": essential_occupation_total,
        "optional_occupation_relation_count": optional_occupation_total
    }

# =========================================================
# Semantic Competency Clustering
# =========================================================
def main():
    print("Loading enriched aggregated profile...")

    data = load_json(INPUT_PATH)

    skills = data["aggregated_skills"]

    # Handle empty competency profiles safely
    if not skills:
        output = {
            "student_id": data.get("student_id", "student_001"),
            "clustering_method": "AgglomerativeClustering",
            "embedding_model": "all-MiniLM-L6-v2",
            "number_of_clusters": 0,
            "clusters": [],
            "note": "No skills were available for clustering."
        }

        save_json(output, OUTPUT_PATH)

        print("No skills available for clustering.")
        print(f"Saved empty clusters to:\n{OUTPUT_PATH}")

        return

    number_of_skills = len(skills)

    # Fallback path when clustering is not meaningful
    if number_of_skills == 1:
        skill = skills[0]

        output = {
            "student_id": data.get("student_id", "student_001"),
            "clustering_method": "SingleSkillFallback",
            "embedding_model": "all-MiniLM-L6-v2",
            "number_of_clusters": 1,
            "clusters": [
                {
                    "cluster_id": 0,
                    "cluster_label": generate_cluster_label([skill]),
                    "skills": [
                        {
                            "esco_uri": skill.get("esco_uri", "-"),
                            "display_title": skill.get(
                                "display_title",
                                skill.get("skill_name", "-")
                            ),
                            "preferred_label": skill.get(
                                "preferred_label",
                                skill.get("skill_name", "-")
                            ),
                            "aggregated_score": skill.get("aggregated_score", 0),
                            "raw_score": skill.get(
                                "raw_score",
                                skill.get("aggregated_score", 0)
                            ),
                            "academic_normalized_score": skill.get(
                                "academic_normalized_score",
                                "-"
                            ),
                            "academic_normalized_percentage": skill.get(
                                "academic_normalized_percentage",
                                "-"
                            ),
                            "relative_rank_score": skill.get(
                                "relative_rank_score",
                                "-"
                            ),
                            "relative_rank_percentage": skill.get(
                                "relative_rank_percentage",
                                "-"
                            ),
                            "competency_level": skill.get("competency_level", "-"),
                            "interpreted_level": skill.get(
                                "interpreted_level",
                                skill.get("competency_level", "-")
                            ),
                            "modules": skill.get("modules", []),
                            "cognitive_levels": skill.get("cognitive_levels", [])
                        }
                    ]
                }
            ],
            "note": "Only one skill was available, so semantic clustering was not required."
        }

        save_json(output, OUTPUT_PATH)

        print("Only one skill available. Saved single-skill fallback cluster.")
        print(f"Saved to:\n{OUTPUT_PATH}")

        return

    if number_of_skills <= 8:
        n_clusters = min(3, number_of_skills)
    elif number_of_skills <= 20:
        n_clusters = 4
    else:
        n_clusters = 6

    # Extract competency labels for embedding generation
    labels = [
        skill.get("display_title", skill.get("skill_name", "Unknown Skill"))
        for skill in skills
    ]

    # Load semantic embedding model
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Creating skill embeddings...")
    embeddings = model.encode(labels)

    print("Clustering skills...")

    effective_clusters = min(n_clusters, number_of_skills)

    # Cluster semantically related competencies
    clustering = AgglomerativeClustering(
        n_clusters=effective_clusters,
        metric="cosine",
        linkage="average"
    )

    cluster_ids = clustering.fit_predict(embeddings)

    # Build structured semantic competency domains
    clusters = {}

    for skill, cluster_id in zip(skills, cluster_ids):
        cluster_key = f"cluster_{cluster_id}"

        if cluster_key not in clusters:
            clusters[cluster_key] = {
                "cluster_id": int(cluster_id),
                "skills": []
            }

        esco_interpretation = skill.get("esco_interpretation", {})

        clusters[cluster_key]["skills"].append({
            "esco_uri": skill.get("esco_uri", "-"),
            "display_title": skill.get(
                "display_title",
                skill.get("preferred_label", "Unknown Skill")
            ),
            "preferred_label": skill.get(
                "preferred_label",
                "Unknown Skill"
            ),

            "aggregated_score": skill.get("aggregated_score", 0),
            "raw_score": skill.get(
                "raw_score",
                skill.get("aggregated_score", 0)
            ),

            "academic_normalized_score": skill.get("academic_normalized_score", "-"),
            "academic_normalized_percentage": skill.get("academic_normalized_percentage", "-"),

            "relative_rank_score": skill.get("relative_rank_score", "-"),
            "relative_rank_percentage": skill.get("relative_rank_percentage", "-"),

            "competency_level": skill.get("competency_level", "-"),
            "interpreted_level": skill.get(
                "interpreted_level",
                skill.get("competency_level", "-")
            ),

            "modules": skill.get("modules", []),
            "cognitive_levels": skill.get("cognitive_levels", []),

            "esco_interpretation": esco_interpretation,

            "skill_type": esco_interpretation.get("skill_type", "Unknown"),
            "reuse_level": esco_interpretation.get("reuse_level", "Unknown"),
            "is_transversal": esco_interpretation.get("is_transversal", False),

            "essential_occupations": esco_interpretation.get("essential_occupations", []),
            "optional_occupations": esco_interpretation.get("optional_occupations", []),
            "essential_occupation_count": esco_interpretation.get("essential_occupation_count", 0),
            "optional_occupation_count": esco_interpretation.get("optional_occupation_count", 0)
        })

    # Final clustered competency domain output
    output = {
        "student_id": data["student_id"],
        "clustering_method": "AgglomerativeClustering",
        "embedding_model": "all-MiniLM-L6-v2",
        "number_of_clusters": effective_clusters,
        "clusters": [
            {
                **cluster,
                "cluster_label": generate_cluster_label(cluster["skills"]),
                "cluster_label_method": "weighted_rule_based_keyword_interpretation",
                "esco_cluster_summary": summarize_cluster_esco_metadata(cluster["skills"])
            }
            for cluster in clusters.values()
        ]
    }

    save_json(output, OUTPUT_PATH)

    print("Skill clustering completed.")
    print(f"Saved to:\n{OUTPUT_PATH}")

    print("\n--- Clusters ---")
    for cluster in output["clusters"]:
        print(f"\nCluster {cluster['cluster_id']}:")
        for skill in cluster["skills"]:
            print(f"- {skill['display_title']}")


if __name__ == "__main__":
    main()