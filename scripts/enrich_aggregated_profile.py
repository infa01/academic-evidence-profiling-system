import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

AGGREGATED_PROFILE_PATH = (
    BASE_DIR / "output" / "student_skill_profile_aggregated.json"
)

ESCO_LOOKUP_PATH = (
    BASE_DIR / "data" / "esco" / "esco_skill_lookup.json"
)

OUTPUT_PATH = (
    BASE_DIR / "output" / "student_skill_profile_aggregated_enriched.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main():
    print("Loading aggregated profile...")
    profile = load_json(AGGREGATED_PROFILE_PATH)

    print("Loading ESCO skill lookup...")
    esco_lookup = load_json(ESCO_LOOKUP_PATH)

    enriched_count = 0
    unresolved_count = 0

    print("Enriching aggregated skills...")

    for skill in profile["aggregated_skills"]:
        esco_uri = skill["esco_uri"]

        preferred_label = esco_lookup.get(esco_uri)

        skill["preferred_label"] = preferred_label

        if preferred_label:
            skill["display_title"] = preferred_label.title()
            enriched_count += 1
        else:
            skill["display_title"] = skill["skill_name"][:60]
            unresolved_count += 1

    save_json(profile, OUTPUT_PATH)

    print("Enrichment completed.")
    print(f"Enriched skills: {enriched_count}")
    print(f"Unresolved skills: {unresolved_count}")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()