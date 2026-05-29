import json
from pathlib import Path

from bloom_semantic_classifier import BloomSemanticClassifier


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def enrich_modules_with_bloom(modules_data):
    classifier = BloomSemanticClassifier()

    for module in modules_data["modules"]:
        for lo in module["learning_outcomes"]:
            lo["bloom"] = classifier.classify(lo["text"])

    return modules_data

def main():
    BASE_DIR = Path(__file__).resolve().parent.parent

    modules_path = BASE_DIR / "data" / "modules.json"

    output_path = (
        BASE_DIR /
        "data" /
        "modules_with_bloom.json"
    )

    modules_data = load_json(modules_path)

    enriched_data = enrich_modules_with_bloom(modules_data)

    save_json(enriched_data, output_path)

    print("Hybrid Bloom mapping completed.")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()