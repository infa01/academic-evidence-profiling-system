import json
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ZIP_PATH = BASE_DIR / "data" / "esco" / "esco_classification_jsonld.zip"


def get_en_label(obj):

    preferred = obj.get("preferredLabel", [])

    if isinstance(preferred, dict):
        preferred = [preferred]

    for item in preferred:

        literal = item.get("literalForm", {})

        if isinstance(literal, dict):

            if "en" in literal:
                return literal["en"]

    return None


def main():
    print(f"Opening: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_file:
        names = zip_file.namelist()

        print("\nFiles inside zip:")
        for name in names:
            print("-", name)

        print("\nSearching for skill objects...")

        found = 0

        for name in names:
            if name == "/" or name.endswith("/"):
                continue

            print(f"\nReading: {name}")

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

                if not uri:
                    continue

                if "/skill/" not in uri:
                    continue

                label = get_en_label(obj)

                print("\n--- SAMPLE SKILL OBJECT ---")
                print("URI:", uri)
                print("Label:", label)
                print("Keys:", list(obj.keys()))

                print("\nRaw object preview:")
                print(json.dumps(obj, indent=2, ensure_ascii=False)[:3000])

                found += 1

                if found >= 3:
                    print("\nDone. Found sample skill objects.")
                    return

        print("\nNo skill objects found.")


if __name__ == "__main__":
    main()
