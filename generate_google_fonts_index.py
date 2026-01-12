import json
import re
from pathlib import Path
import argparse

LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
RAW_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"


def parse_metadata(file_path: Path, license_type: str):
    content = file_path.read_text(encoding="utf-8")

    def get_value(key: str):
        match = re.search(rf'^{key}:\s*"(.*?)"', content, re.M)
        return match.group(1) if match else ""

    fonts = []
    font_blocks = re.findall(r"fonts\s*\{(.*?)\}", content, re.S)

    for block in font_blocks:
        file_match = re.search(r'filename: "(.*?)"', block)

        if file_match:
            font_filename = file_match.group(1)
            family_dir = file_path.parent.name

            fonts.append(f"{RAW_BASE_URL}/{license_type}/{family_dir}/{font_filename}")

    return {
        "family": get_value("name"),
        "category": get_value("category"),
        "subsets": re.findall(r'^subsets: "(.*?)"', content, re.M),
        "fonts": fonts,
    }


def main(repo_path: Path, output_path: Path):
    db = []

    for folder in LICENSE_FOLDERS:
        license_path = repo_path / folder

        if not license_path.exists():
            continue

        for metadata_path in license_path.glob("*/METADATA.pb"):
            try:
                family_data = parse_metadata(metadata_path, folder)
                if family_data["family"]:
                    db.append(family_data)
            except Exception as e:
                print(f"Skipping {metadata_path}: {e}")
                continue

    db.sort(key=lambda f: f["family"].lower())

    output_path.write_text(
        json.dumps(db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Done! Indexed {len(db)} families.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Google Fonts metadata.")

    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to the root of the google/fonts repository",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("google_fonts_index.json"),
        help="Output JSON file path (default: google_fonts_index.json)",
    )

    args = parser.parse_args()

    main(args.repo_path, args.output)
