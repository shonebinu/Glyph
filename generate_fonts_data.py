import json
import re
import argparse
import io
import concurrent.futures
from pathlib import Path
from typing import List
from fontTools.ttLib import TTFont, TTCollection
from fontTools.subset import Subsetter


LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_TTC_PATH = "previews.ttc"


def subset_single_font(ttf_path: Path, text: str):
    try:
        subsetter = Subsetter()
        subsetter.populate(text=text)

        with TTFont(ttf_path, lazy=True) as font:
            subsetter.subset(font)

            buf = io.BytesIO()
            font.save(buf)
            return buf.getvalue(), ttf_path
    except Exception as e:
        print(f"Skipping {ttf_path.name}: {e}")
        return None, ttf_path


def generate_combined_subsets_ttc_parallel(files: List[Path], text: str, output: Path):
    fonts = []
    failed_paths = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_ttf = {
            executor.submit(subset_single_font, ttf, text): ttf for ttf in files
        }

        for future in concurrent.futures.as_completed(future_to_ttf):
            font_bytes, original_path = future.result()
            if font_bytes:
                fonts.append(TTFont(io.BytesIO(font_bytes)))
            else:
                failed_paths.append(original_path)

    ttc = TTCollection()
    ttc.fonts = fonts
    ttc.save(output)

    print(f"\n{len(failed_paths)} files failed to subset:")

    for path in failed_paths:
        print(path)

    return len(fonts)


def parse_metadata(metadata_path: Path):
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
                    "weight": int(weight),
                    "filename": filename,
                    "url": f"{FONT_FILE_BASE_URL}/{license.lower()}/{family_dir.name}/{filename}",
                }
            )

    metadata = {
        "family": family,
        "designer": designer,
        "license": license,
        "category": category,
        "subsets": subsets,
        "font_files": font_files,
        "is_variable": "axes {" in content,
    }

    best_file = next(
        (
            item["filename"]
            for item in font_files
            if item["style"] == "normal" and item["weight"] == 400
        ),
        font_files[0]["filename"] if font_files else None,
    )

    best_file_path = family_dir / best_file if best_file else None

    return metadata, best_file_path


def main(gfonts_path: Path):
    db = []
    best_files = []
    ttc_count = 0

    for folder in LICENSE_FOLDERS:
        license_path = gfonts_path / folder

        if not license_path.exists():
            continue

        for metadata_path in license_path.glob("*/METADATA.pb"):
            try:
                family_data, best_file = parse_metadata(metadata_path)
                db.append(family_data)

                if best_file:
                    best_files.append(best_file)
            except Exception as e:
                print(f"Skipping metadata extraction {metadata_path}: {e}")
                continue

    db.sort(key=lambda f: f["family"].lower())

    Path(OUTPUT_JSON_PATH).write_text(
        json.dumps(db, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ttc_count = generate_combined_subsets_ttc_parallel(
        best_files,
        "The quick brown fox jumps over the lazy dog.",
        Path(OUTPUT_TTC_PATH),
    )

    print(
        f"\nDone! Indexed {len(db)} families. {OUTPUT_TTC_PATH} includes {ttc_count} fonts subset."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Index Google Fonts and generate preview fonts collection."
    )

    parser.add_argument(
        "google_fonts_path",
        type=Path,
        help="Path to the root of the google fonts repository",
    )

    args = parser.parse_args()

    main(args.google_fonts_path)
