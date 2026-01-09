import json
import re
from pathlib import Path

import brotli

REPO_PATH = Path("./google_fonts")
LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
RAW_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"


def parse_metadata(file_path, license_type):
    content = file_path.read_text(encoding="utf-8")

    def get_value(key):
        match = re.search(rf'^{key}:\s*"(.*?)"', content, re.M)
        return match.group(1) if match else ""

    fonts = []
    font_blocks = re.findall(r"fonts\s*\{(.*?)\}", content, re.S)

    for block in font_blocks:
        style_match = re.search(r'style: "(.*?)"', block)
        weight_match = re.search(r"weight: (\d+)", block)
        file_match = re.search(r'filename: "(.*?)"', block)

        if all([style_match, weight_match, file_match]):
            font_filename = file_match.group(1)
            family_dir = file_path.parent.name

            fonts.append(
                {
                    "weight": int(weight_match.group(1)),
                    "style": style_match.group(1),
                    "url": f"{RAW_BASE_URL}/{license_type}/{family_dir}/{font_filename}",
                }
            )

    return {
        "family": get_value("name"),
        "category": get_value("category"),
        "subsets": re.findall(r'^subsets: "(.*?)"', content, re.M),
        "fonts": fonts,
    }


def main():
    db = []

    for folder in LICENSE_FOLDERS:
        license_path = REPO_PATH / folder

        for metadata_path in license_path.glob("*/METADATA.pb"):
            try:
                family_data = parse_metadata(metadata_path, folder)
                db.append(family_data)
            except Exception:
                continue

    db.sort(key=lambda f: f["family"].lower())

    Path("fonts_index.json").write_text(json.dumps(db, indent=2), encoding="utf-8")

    compact_json = json.dumps(db, separators=(",", ":")).encode("utf-8")
    compressed_data = brotli.compress(compact_json, quality=11)

    Path("fonts_index.json.br").write_bytes(compressed_data)

    print(f"Done! Indexed {len(db)} families.")


if __name__ == "__main__":
    main()
