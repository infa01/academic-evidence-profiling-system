import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PROFILE_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_calibrated.json"
)

ESCO_LOOKUP_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_interpretation_lookup.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_esco_interpreted.json"
)


MAX_OCCUPATIONS_PER_SKILL = 5


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def limit_occupations(occupations, limit=MAX_OCCUPATIONS_PER_SKILL):
    return occupations[:limit]


def build_esco_interpretation(skill, esco_skills_lookup):
    esco_uri = skill.get("esco_uri")

    lookup_entry = esco_skills_lookup.get(esco_uri)

    if not lookup_entry:
        return {
            "found_in_esco_lookup": False,
            "skill_type": "Unknown",
            "reuse_level": "Unknown",
            "is_transversal": False,
            "essential_occupation_count": 0,
            "optional_occupation_count": 0,
            "essential_occupations": [],
            "optional_occupations": []
        }

    essential_occupations = lookup_entry.get(
        "essential_occupations",
        []
    )

    optional_occupations = lookup_entry.get(
        "optional_occupations",
        []
    )

    return {
        "found_in_esco_lookup": True,

        "preferred_label": lookup_entry.get(
            "preferred_label",
            skill.get("display_title", skill.get("skill_name", "-"))
        ),

        "skill_type": lookup_entry.get("skill_type", "Unknown"),
        "skill_type_uri": lookup_entry.get("skill_type_uri"),

        "reuse_level": lookup_entry.get("reuse_level", "Unknown"),
        "reuse_level_uri": lookup_entry.get("reuse_level_uri"),

        "is_transversal": lookup_entry.get("is_transversal", False),

        "broader": lookup_entry.get("broader", []),
        "broader_transitive": lookup_entry.get("broader_transitive", []),

        "essential_occupation_count": lookup_entry.get(
            "essential_occupation_count",
            len(essential_occupations)
        ),

        "optional_occupation_count": lookup_entry.get(
            "optional_occupation_count",
            len(optional_occupations)
        ),

        "essential_occupations": limit_occupations(
            essential_occupations
        ),

        "optional_occupations": limit_occupations(
            optional_occupations
        )
    }


def main():
    print("Loading enriched aggregated student profile...")

    if not INPUT_PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"Input profile not found: {INPUT_PROFILE_PATH}"
        )

    profile = load_json(INPUT_PROFILE_PATH)

    print("Loading ESCO interpretation lookup...")

    if not ESCO_LOOKUP_PATH.exists():
        raise FileNotFoundError(
            f"ESCO interpretation lookup not found: {ESCO_LOOKUP_PATH}"
        )

    esco_lookup = load_json(ESCO_LOOKUP_PATH)
    esco_skills_lookup = esco_lookup.get("skills", {})

    skills = profile.get("aggregated_skills", [])

    interpreted_skills = []

    found_count = 0
    transversal_count = 0
    skills_with_occupations = 0

    print("Interpreting ESCO concepts...")

    for skill in skills:
        interpretation = build_esco_interpretation(
            skill,
            esco_skills_lookup
        )

        if interpretation.get("found_in_esco_lookup"):
            found_count += 1

        if interpretation.get("is_transversal"):
            transversal_count += 1

        total_occupation_count = (
            interpretation.get("essential_occupation_count", 0)
            + interpretation.get("optional_occupation_count", 0)
        )

        if total_occupation_count > 0:
            skills_with_occupations += 1

        interpreted_skill = {
            **skill,
            "esco_interpretation": interpretation
        }

        interpreted_skills.append(interpreted_skill)

    output = {
        **profile,
        "aggregated_skills": interpreted_skills,
        "esco_interpretation_summary": {
            "total_skills": len(interpreted_skills),
            "skills_found_in_esco_lookup": found_count,
            "transversal_skills": transversal_count,
            "skills_with_occupation_relations": skills_with_occupations,
            "source_lookup": str(ESCO_LOOKUP_PATH)
        }
    }

    save_json(output, OUTPUT_PATH)

    print("ESCO concept interpretation completed.")
    print(f"Saved to:\n{OUTPUT_PATH}")

    print("\n--- ESCO Interpretation Summary ---")
    print(f"Total skills: {len(interpreted_skills)}")
    print(f"Found in ESCO lookup: {found_count}")
    print(f"Transversal skills: {transversal_count}")
    print(f"Skills with occupation relations: {skills_with_occupations}")


if __name__ == "__main__":
    main()