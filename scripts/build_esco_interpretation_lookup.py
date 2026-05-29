import json
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ESCO_ZIP_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_classification_jsonld.zip"
)

ESCO_SKILL_LABELS_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_skill_lookup.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_interpretation_lookup.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def simplify_uri_value(uri):
    if not uri:
        return "Unknown"

    return uri.rstrip("/").split("/")[-1]


def build_literal_label_lookup(concepts):
    label_lookup = {}

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        uri = concept.get("uri")
        literal_form = concept.get("literalForm")

        if not uri or not isinstance(literal_form, dict):
            continue

        english_label = literal_form.get("en")

        if english_label:
            label_lookup[uri] = english_label

    return label_lookup


def resolve_label_object(label_object, label_lookup, fallback="Unknown"):
    if isinstance(label_object, str):
        return label_lookup.get(label_object, fallback)

    if isinstance(label_object, dict):
        literal_form = label_object.get("literalForm")

        if isinstance(literal_form, dict):
            english_label = literal_form.get("en")

            if english_label:
                return english_label

        label_uri = label_object.get("uri")

        if isinstance(label_uri, str):
            return label_lookup.get(label_uri, fallback)

    return fallback


def resolve_preferred_label(concept, label_lookup, fallback="Unknown"):
    preferred_label = concept.get("preferredLabel")

    if isinstance(preferred_label, list):
        for label_object in preferred_label:
            resolved_label = resolve_label_object(
                label_object,
                label_lookup,
                fallback=None
            )

            if resolved_label:
                return resolved_label

        return fallback

    return resolve_label_object(
        preferred_label,
        label_lookup,
        fallback
    )


def get_concepts_from_zip(zip_path):
    print("Opening ESCO classification zip...")

    if not zip_path.exists():
        raise FileNotFoundError(f"ESCO zip not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        jsonld_files = [
            file_name
            for file_name in zip_file.namelist()
            if file_name.endswith(".json-ld")
        ]

        if not jsonld_files:
            raise FileNotFoundError("No .json-ld file found inside ESCO zip.")

        jsonld_name = jsonld_files[0]

        print(f"Found JSON-LD file: {jsonld_name}")
        print("Loading ESCO JSON-LD. This may take a moment...")

        with zip_file.open(jsonld_name) as file:
            data = json.load(file)

    if isinstance(data, dict) and "@graph" in data:
        return data["@graph"]

    if isinstance(data, list):
        return data

    raise ValueError(
        "Unexpected ESCO JSON-LD structure. Expected list or dictionary with '@graph'."
    )


def is_occupation_uri(uri):
    return isinstance(uri, str) and "/occupation/" in uri


def build_occupation_lookup(concepts, label_lookup):
    occupations = {}

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        uri = concept.get("uri", "")

        if "/occupation/" not in uri:
            continue

        occupations[uri] = {
            "uri": uri,
            "preferred_label": resolve_preferred_label(
                concept,
                label_lookup,
                "Unknown occupation"
            ),
            "broader": as_list(concept.get("broader")),
            "broader_transitive": as_list(concept.get("broaderTransitive")),
            "related_essential_skills": as_list(
                concept.get("relatedEssentialSkill")
            ),
            "related_optional_skills": as_list(
                concept.get("relatedOptionalSkill")
            )
        }

    return occupations


def build_skill_lookup(concepts, skill_labels, occupation_lookup):
    skills = {}

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        uri = concept.get("uri", "")

        if "/skill/" not in uri:
            continue

        skill_type_uri = concept.get("skillType")
        reuse_level_uri = concept.get("skillReuseLevel")

        skill_type = simplify_uri_value(skill_type_uri)
        reuse_level = simplify_uri_value(reuse_level_uri)

        broader = as_list(concept.get("broader"))
        broader_transitive = as_list(concept.get("broaderTransitive"))

        essential_occupation_uris = [
            uri for uri in as_list(concept.get("isEssentialSkillFor"))
            if is_occupation_uri(uri)
        ]

        optional_occupation_uris = [
            uri for uri in as_list(concept.get("isOptionalSkillFor"))
            if is_occupation_uri(uri)
        ]

        essential_occupations = [
            {
                "occupation_uri": occupation_uri,
                "occupation_label": occupation_lookup.get(
                    occupation_uri,
                    {}
                ).get("preferred_label", "Unknown occupation"),
                "relation_type": "essential"
            }
            for occupation_uri in essential_occupation_uris
        ]

        optional_occupations = [
            {
                "occupation_uri": occupation_uri,
                "occupation_label": occupation_lookup.get(
                    occupation_uri,
                    {}
                ).get("preferred_label", "Unknown occupation"),
                "relation_type": "optional"
            }
            for occupation_uri in optional_occupation_uris
        ]

        is_transversal = (
            reuse_level == "transversal"
            or "http://data.europa.eu/esco/skill/04a13491-b58c-4d33-8b59-8fad0d55fe9e"
            in broader_transitive
            or skill_labels.get(uri, "").lower() == "transversal skills and competences"
        )

        skills[uri] = {
            "uri": uri,
            "preferred_label": skill_labels.get(uri, "Unknown skill"),

            "skill_type_uri": skill_type_uri,
            "skill_type": skill_type,

            "reuse_level_uri": reuse_level_uri,
            "reuse_level": reuse_level,

            "is_transversal": is_transversal,

            "broader": broader,
            "broader_transitive": broader_transitive,

            "essential_occupations": essential_occupations,
            "optional_occupations": optional_occupations,

            "essential_occupation_count": len(essential_occupations),
            "optional_occupation_count": len(optional_occupations)
        }

    return skills


def main():
    print("Loading ESCO skill label lookup...")

    if not ESCO_SKILL_LABELS_PATH.exists():
        raise FileNotFoundError(
            f"ESCO skill labels not found: {ESCO_SKILL_LABELS_PATH}"
        )

    skill_labels = load_json(ESCO_SKILL_LABELS_PATH)

    concepts = get_concepts_from_zip(ESCO_ZIP_PATH)

    print("Building label lookup...")
    label_lookup = build_literal_label_lookup(concepts)

    print("Building occupation lookup...")
    occupations = build_occupation_lookup(concepts, label_lookup)

    print("Building skill interpretation lookup...")
    skills = build_skill_lookup(
        concepts=concepts,
        skill_labels=skill_labels,
        occupation_lookup=occupations
    )

    output = {
        "metadata": {
            "source": "ESCO v1.2.1 JSON-LD",
            "purpose": "Compact lookup for ESCO concept interpretation and occupation-oriented evidence.",
            "skill_count": len(skills),
            "occupation_count": len(occupations)
        },
        "skills": skills,
        "occupations": occupations
    }

    save_json(output, OUTPUT_PATH)

    print("ESCO interpretation lookup generated.")
    print(f"Saved to:\n{OUTPUT_PATH}")

    print("\n--- Summary ---")
    print(f"Skills: {len(skills)}")
    print(f"Occupations: {len(occupations)}")

    skills_with_type = sum(
        1 for skill in skills.values()
        if skill.get("skill_type") != "Unknown"
    )

    skills_with_reuse = sum(
        1 for skill in skills.values()
        if skill.get("reuse_level") != "Unknown"
    )

    skills_with_occupations = sum(
        1 for skill in skills.values()
        if skill.get("essential_occupation_count", 0) > 0
        or skill.get("optional_occupation_count", 0) > 0
    )

    transversal_skills = sum(
        1 for skill in skills.values()
        if skill.get("is_transversal")
    )

    print(f"Skills with skill type: {skills_with_type}")
    print(f"Skills with reuse level: {skills_with_reuse}")
    print(f"Skills linked to occupations: {skills_with_occupations}")
    print(f"Transversal skills detected: {transversal_skills}")


if __name__ == "__main__":
    main()