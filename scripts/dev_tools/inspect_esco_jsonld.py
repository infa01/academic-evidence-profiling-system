import json
import zipfile
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parents[2]

ZIP_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_classification_jsonld.zip"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "esco_jsonld_inspection_report.json"
)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_english_label(concept):
    label = concept.get("preferredLabel", {})

    if isinstance(label, dict):
        literal_form = label.get("literalForm", {})

        if isinstance(literal_form, dict):
            return literal_form.get("en", "-")

    return "-"


def as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def main():
    print("Opening ESCO JSON-LD zip...")

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"ESCO zip not found: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_file:
        zip_files = zip_file.namelist()

        jsonld_files = [
            file_name
            for file_name in zip_files
            if file_name.endswith(".json-ld")
        ]

        if not jsonld_files:
            raise FileNotFoundError("No .json-ld file found inside zip.")

        jsonld_name = jsonld_files[0]

        print(f"Found JSON-LD file: {jsonld_name}")
        print("Loading JSON-LD data. This may take a moment...")

        with zip_file.open(jsonld_name) as file:
            data = json.load(file)

    print("Inspecting ESCO concepts...")

    if isinstance(data, dict) and "@graph" in data:
        concepts = data["@graph"]
    elif isinstance(data, list):
        concepts = data
    else:
        raise ValueError(
            "Unexpected JSON-LD structure. Expected a list or a dictionary with '@graph'."
        )

    concept_count = len(concepts)

    type_counter = Counter()
    uri_prefix_counter = Counter()

    field_counter = Counter()

    skill_concepts = []
    occupation_concepts = []

    skill_type_count = 0
    skill_reuse_level_count = 0
    broader_count = 0
    broader_transitive_count = 0
    essential_skill_for_count = 0
    optional_skill_for_count = 0
    related_essential_skill_count = 0
    related_optional_skill_count = 0

    sample_skills = []
    sample_occupations = []

    for concept in concepts:
        if not isinstance(concept, dict):
            continue

        uri = concept.get("uri", "")

        concept_types = as_list(concept.get("type"))

        for concept_type in concept_types:
            type_counter[concept_type] += 1

        for field in concept.keys():
            field_counter[field] += 1

        if "/skill/" in uri:
            skill_concepts.append(concept)
            uri_prefix_counter["skill"] += 1

            if concept.get("skillType"):
                skill_type_count += 1

            if concept.get("skillReuseLevel"):
                skill_reuse_level_count += 1

            if concept.get("broader"):
                broader_count += 1

            if concept.get("broaderTransitive"):
                broader_transitive_count += 1

            if concept.get("isEssentialSkillFor"):
                essential_skill_for_count += 1

            if concept.get("isOptionalSkillFor"):
                optional_skill_for_count += 1

            if concept.get("relatedEssentialSkill"):
                related_essential_skill_count += 1

            if concept.get("relatedOptionalSkill"):
                related_optional_skill_count += 1

            if len(sample_skills) < 5:
                sample_skills.append({
                    "uri": uri,
                    "label": get_english_label(concept),
                    "type": concept.get("type"),
                    "skillType": concept.get("skillType"),
                    "skillReuseLevel": concept.get("skillReuseLevel"),
                    "broader": concept.get("broader"),
                    "broaderTransitive": concept.get("broaderTransitive"),
                    "isEssentialSkillFor_count": len(as_list(concept.get("isEssentialSkillFor"))),
                    "isOptionalSkillFor_count": len(as_list(concept.get("isOptionalSkillFor")))
                })

        elif "/occupation/" in uri:
            occupation_concepts.append(concept)
            uri_prefix_counter["occupation"] += 1

            if len(sample_occupations) < 5:
                sample_occupations.append({
                    "uri": uri,
                    "label": get_english_label(concept),
                    "type": concept.get("type"),
                    "broader": concept.get("broader"),
                    "broaderTransitive": concept.get("broaderTransitive"),
                    "relatedEssentialSkill_count": len(as_list(concept.get("relatedEssentialSkill"))),
                    "relatedOptionalSkill_count": len(as_list(concept.get("relatedOptionalSkill")))
                })

        else:
            uri_prefix_counter["other"] += 1

    report = {
        "source_zip": str(ZIP_PATH),
        "jsonld_file_inside_zip": jsonld_name,
        "total_concepts": concept_count,

        "uri_prefix_counts": dict(uri_prefix_counter),
        "type_counts": dict(type_counter.most_common()),
        "top_fields": dict(field_counter.most_common(50)),

        "skill_statistics": {
            "total_skill_concepts": len(skill_concepts),
            "with_skillType": skill_type_count,
            "with_skillReuseLevel": skill_reuse_level_count,
            "with_broader": broader_count,
            "with_broaderTransitive": broader_transitive_count,
            "with_isEssentialSkillFor": essential_skill_for_count,
            "with_isOptionalSkillFor": optional_skill_for_count,
            "with_relatedEssentialSkill": related_essential_skill_count,
            "with_relatedOptionalSkill": related_optional_skill_count
        },

        "occupation_statistics": {
            "total_occupation_concepts": len(occupation_concepts)
        },

        "sample_skills": sample_skills,
        "sample_occupations": sample_occupations
    }

    save_json(report, OUTPUT_PATH)

    print("ESCO inspection completed.")
    print(f"Saved report to:\n{OUTPUT_PATH}")

    print("\n--- Summary ---")
    print(f"Total concepts: {concept_count}")
    print(f"Skills: {len(skill_concepts)}")
    print(f"Occupations: {len(occupation_concepts)}")
    print(f"Skills with skillType: {skill_type_count}")
    print(f"Skills with skillReuseLevel: {skill_reuse_level_count}")
    print(f"Skills with essential occupation relations: {essential_skill_for_count}")
    print(f"Skills with optional occupation relations: {optional_skill_for_count}")


if __name__ == "__main__":
    main()
