import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from methodology_config import (
    EMBEDDING_MODEL_NAME,
    SIMILARITY_THRESHOLD,
    get_semantic_match_note,
    interpret_semantic_match
)

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "output" / "modules_with_bloom_esco.json"
OUTPUT_PATH = BASE_DIR / "output" / "modules_with_bloom_esco_filtered.json"
ESCO_LOOKUP_PATH = BASE_DIR / "data" / "esco" / "esco_skill_lookup.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
    
def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def calculate_similarity(model, text_a, text_b):
    embeddings = model.encode([text_a, text_b])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score), 4)

def title_case_skill(label):
    if not label:
        return "Unknown ESCO Skill"

    small_words = {
        "and", "or", "of", "for", "to", "in", "on", "with",
        "the", "a", "an", "by", "from"
    }

    words = label.replace("_", " ").split()
    titled_words = []

    for index, word in enumerate(words):
        lower_word = word.lower()

        if index > 0 and lower_word in small_words:
            titled_words.append(lower_word)
        else:
            titled_words.append(lower_word.capitalize())

    return " ".join(titled_words)

def main():
    print("Loading ESCO-enriched dataset...")
    data = load_json(INPUT_PATH)

    print("Loading ESCO Lookup...")
    esco_lookup = load_json(ESCO_LOOKUP_PATH)

    print("Loading semantic similarity model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Calculating similarity scores...")

    for module in data["modules"]:
        print(f"Processing module: {module['module_code']}")

        for lo in module["learning_outcomes"]:
            lo_text = lo["text"]

            skills = lo.get("esco", {}).get("skills", [])

            evaluated_skills = []

            for skill in skills:
                skill_text = skill["name"]

                similarity_score = calculate_similarity(
                    model,
                    lo_text,
                    skill_text
                )

                skill["similarity_score"] = similarity_score
                skill["semantic_match_quality"] = interpret_semantic_match(
                    similarity_score
                )
                skill["semantic_match_note"] = get_semantic_match_note(
                    skill["semantic_match_quality"]
                )
                skill["retained_after_similarity_filter"] = (
                    similarity_score >= SIMILARITY_THRESHOLD
                )

                evaluated_skills.append(skill)

            evaluated_skills.sort(
                key=lambda item: item.get("similarity_score", 0),
                reverse=True
            )

            filtered_skills = []

            for rank, skill in enumerate(evaluated_skills, start=1):
                skill["candidate_rank_by_similarity"] = rank

                if skill.get("similarity_score", 0) >= SIMILARITY_THRESHOLD:
                    esco_uri = skill.get("uri")
                    preferred_label = esco_lookup.get(esco_uri)

                    skill["preferred_label"] = preferred_label

                    if preferred_label:
                        skill["display_title"] = title_case_skill(preferred_label)
                    else:
                        skill["display_title"] = skill.get(
                            "name",
                            "Unknown Skill"
                        )[:80]

                    filtered_skills.append(skill)

            filtered_skills.sort(
                key=lambda item: item.get("similarity_score", 0),
                reverse=True
            )

            lo["esco"]["skills"] = filtered_skills
            
            lo["esco"]["number_of_skills"] = len(filtered_skills)

            lo["esco"]["similarity_threshold"] = SIMILARITY_THRESHOLD
            lo["esco"]["evaluated_skill_count"] = len(evaluated_skills)
            lo["esco"]["rejected_below_threshold_count"] = (
                len(evaluated_skills) - len(filtered_skills)
            )
            lo["esco"]["match_quality_counts"] = {
                "strong_semantic_match": sum(
                    1
                    for skill in filtered_skills
                    if skill.get("semantic_match_quality") == "strong_semantic_match"
                ),
                "supporting_semantic_match": sum(
                    1
                    for skill in filtered_skills
                    if skill.get("semantic_match_quality") == "supporting_semantic_match"
                ),
                "borderline_semantic_match": sum(
                    1
                    for skill in filtered_skills
                    if skill.get("semantic_match_quality") == "borderline_semantic_match"
                )
            }
    
    save_json(data, OUTPUT_PATH)

    print("Semantic scoring completed.")
    print(f"Output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
