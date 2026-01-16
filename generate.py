import argparse
import json
import re
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_SUBSETS_FOLDER_PATH = "subsets"


def generate_subset_ttf(font_path: Path, text: str, output_ttf_path: Path):
    try:
        subsetter = Subsetter(options=Options())
        subsetter.populate(text=text)

        font = TTFont(font_path, lazy=True)
        subsetter.subset(font)

        font.save(output_ttf_path)
        font.close()

        return True
    except Exception as e:
        print(f"Error generating subset: {e}")
        return False


def parse_metadata(metadata_path: Path, license_type: str):
    def get_value(key: str):
        match = re.search(rf'^{key}:\s*"(.*?)"', content, re.M)
        return match.group(1) if match else ""

    content = metadata_path.read_text(encoding="utf-8")
    family_dir = metadata_path.parent

    family = get_value("name")
    category = get_value("category")
    designer = get_value("designer")
    license = get_value("license")
    subsets = re.findall(r'^subsets: "(.*?)"', content, re.M)

    font_blocks = re.findall(r"fonts\s*\{(.*?)\}", content, re.S)
    font_files = []

    for block in font_blocks:
        file_match = re.search(r'filename: "(.*?)"', block)
        style_match = re.search(r'style: "(.*?)"', block)
        weight_match = re.search(r"weight: (\d+)", block)

        if file_match and style_match and weight_match:
            filename = file_match.group(1)
            style = style_match.group(1)
            weight = weight_match.group(1)

            font_files.append(
                {
                    "style": style,
                    "weight": weight,
                    "filename": filename,
                    "url": f"{FONT_FILE_BASE_URL}/{license_type}/{family_dir.name}/{filename}",
                }
            )

    preview_font = None
    preview_rel_path = None

    for item in font_files:
        if item["style"] == "normal" and item["weight"] == "400":
            preview_font = item["filename"]
            break

    if not preview_font and font_files:
        preview_font = font_files[0]["filename"]

    if preview_font:
        font_path = family_dir / preview_font
        subsets_folder = Path(OUTPUT_SUBSETS_FOLDER_PATH)
        svg_filename = f"{family_dir.name}.svg"
        svg_dest = subsets_folder / svg_filename

        if generate_subset_ttf(
            font_path, "The quick brown fox jumps over the lazy dog.", svg_dest
        ):
            preview_rel_path = f"{subsets_folder.name}/{svg_filename}"

    return {
        "family": family,
        "designer": designer,
        "license": license,
        "category": category,
        "subsets": subsets,
        "font_urls": font_files,
        "preview": preview_rel_path,
        "is_variable": "axes {" in content,
    }


def main(gfonts_path: Path):
    Path(OUTPUT_SUBSETS_FOLDER_PATH).mkdir(exist_ok=True)

    db = []

    for folder in LICENSE_FOLDERS:
        license_path = gfonts_path / folder

        if not license_path.exists():
            continue

        for metadata_path in license_path.glob("*/METADATA.pb"):
            try:
                family_data = parse_metadata(metadata_path, folder)
                db.append(family_data)
            except Exception as e:
                print(f"Skipping {metadata_path}: {e}")
                continue

    db.sort(key=lambda f: f["family"].lower())

    Path(OUTPUT_JSON_PATH).write_text(
        json.dumps(db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Done! Indexed {len(db)} families.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Google Fonts.")

    parser.add_argument(
        "gfonts_path",
        type=Path,
        help="Path to the root of the google fonts repository",
    )

    args = parser.parse_args()

    main(args.gfonts_path)
