import json
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "output" / "modules_with_bloom_esco_filtered.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    data = load_json(INPUT_PATH)

    total_modules = 0
    total_los = 0
    los_with_skills = 0
    los_without_skills = 0
    total_skills = 0

    skills_counter = Counter()

    print("Analysing filtered dataset...\n")

    for module in data["modules"]:
        total_modules += 1

        module_skill_count = 0
        module_lo_count = len(module["learning_outcomes"])

        for lo in module["learning_outcomes"]:
            total_los += 1

            skills = lo.get("esco", {}).get("skills", [])

            if skills:
                los_with_skills += 1
            else:
                los_without_skills += 1

            total_skills += len(skills)
            module_skill_count += len(skills)

            for skill in skills:
                skills_counter[skill["name"]] += 1

        print(
            f"{module['module_code']} - "
            f"{module['module_title']}: "
            f"{module_skill_count} skills across {module_lo_count} LOs"
        )

    print("\n--- Overall Summary ---")
    print(f"Total modules: {total_modules}")
    print(f"Total learning outcomes: {total_los}")
    print(f"Learning outcomes with skills: {los_with_skills}")
    print(f"Learning outcomes without skills: {los_without_skills}")
    print(f"Total accepted ESCO skills: {total_skills}")

    print("\n--- Top 10 Extracted Skills ---")
    for skill_name, count in skills_counter.most_common(10):
        print(f"{count}x - {skill_name[:100]}...")


if __name__ == "__main__":
    main()
