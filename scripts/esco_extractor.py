import json
from pathlib import Path
from esco_skill_extractor import SkillExtractor

BASE_DIR = Path(__file__).resolve().parent.parent

input_path = BASE_DIR / "data" / "modules_with_bloom.json"
output_path = BASE_DIR / "output" / "modules_with_bloom_esco.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
    
def save_json(data, path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def main():
    print("Loading modules with Bloom data...")
    data = load_json(input_path)

    print("Initialising ESCO skill extractor...")
    extractor = SkillExtractor()

    #print(type(extractor._skills))
    #print(list(extractor._skills.items())[:3])
    skills_lookup = dict(
        zip(extractor._skills["id"], extractor._skills["description"])
    )

    print("Extracting ESCO skills from learning outcomes...")

    for module in data["modules"]:
        print(f"Processing module: {module['module_code']}")

        for lo in module["learning_outcomes"]:
            lo_text = lo["text"]

            results = extractor.get_skills([lo_text])
            skill_uris = results[0]
            resolved_skills = []

            for uri in skill_uris:
                skill_name = skills_lookup.get(uri, "Unknown Skill")

                resolved_skills.append({
                    "uri": uri,
                    "name": skill_name
                })

            lo["esco"] = {
                "method": "esco-skill-extractor",
                "skills": resolved_skills,
                "number_of_skills": len(resolved_skills)
            }

    save_json(data, output_path)

    print("ESCO extraction completed.")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()