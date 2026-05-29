import json
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ZIP_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_classification_jsonld.zip"
)

OUTPUT_PATH = (
    BASE_DIR /
    "data" /
    "esco" /
    "esco_skill_lookup.json"
)


def get_en_label(obj):
    preferred = obj.get("preferredLabel", [])

    if isinstance(preferred, dict):
        preferred = [preferred]

    for item in preferred:
        literal = item.get("literalForm", {})

        if isinstance(literal, dict) and "en" in literal:
            return literal["en"]

    return None


def main():
    print("Building ESCO skill lookup...")

    lookup = {}

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_file:
        names = zip_file.namelist()

        for name in names:
            if name == "/" or name.endswith("/"):
                continue

            print(f"Reading: {name}")

            with zip_file.open(name) as file:
                data = json.load(file)

            if isinstance(data, dict):
                objects = data.get("@graph", data.get("graph", [data]))

                if isinstance(objects, dict):
                    objects = [objects]

            elif isinstance(data, list):
                objects = data

            else:
                continue

            for obj in objects:
                uri = obj.get("uri") or obj.get("@id")

                if not uri or "/skill/" not in uri:
                    continue

                label = get_en_label(obj)

                if label:
                    lookup[uri] = label

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(lookup, file, indent=2, ensure_ascii=False)

    print("ESCO lookup generated.")
    print(f"Total skills: {len(lookup)}")
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()