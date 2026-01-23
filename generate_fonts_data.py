# https://googlefonts.github.io/gf-guide/metadata.html

import json
import argparse
import io
import concurrent.futures
from pathlib import Path
from typing import List, Tuple
from fontTools.ttLib import TTFont, TTCollection
from fontTools.subset import Subsetter
from google.protobuf import text_format
from gftools import fonts_public_pb2
from google.protobuf.json_format import MessageToDict
from gflanguages import LoadLanguages

LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_TTC_PATH = "previews.ttc"


gflanguages = LoadLanguages()


def subset_single_font(ttf_path: Path, text: str):
    try:
        subsetter = Subsetter()
        subsetter.populate(text=text)

        with TTFont(ttf_path, lazy=True) as font:
            subsetter.subset(font)

            buf = io.BytesIO()
            font.save(buf)
            return buf.getvalue()
    except Exception as e:
        print(f"Skipping {ttf_path.name}: {e}")
        return None


def generate_preview_subsets_ttc_parallel(
    preview_samples: List[Tuple[Path, str]], output: Path
):
    fonts = []
    failed_paths = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_ttf = {
            executor.submit(subset_single_font, ttf_path, preview_string): ttf_path
            for ttf_path, preview_string in preview_samples
        }

        total = len(future_to_ttf)
        completed = 0

        for future in concurrent.futures.as_completed(future_to_ttf):
            completed += 1
            font_bytes = future.result()
            if font_bytes:
                fonts.append(TTFont(io.BytesIO(font_bytes)))
            else:
                failed_paths.append(future_to_ttf[future])

            print(f"{completed} out of {total} done subsetting")

    ttc = TTCollection()
    ttc.fonts = fonts
    ttc.save(output)

    print(f"\n{len(failed_paths)} files failed to subset:")

    for path in failed_paths:
        print(path)

    return len(fonts)


def load_metadata(path: Path):
    message = fonts_public_pb2.FamilyProto()
    text_format.Parse(path.read_text(), message, allow_unknown_field=True)
    return MessageToDict(message, preserving_proto_field_name=True)


def get_best_preview_string(metadata):
    if "sample_text" in metadata and "styles" in metadata["sample_text"]:
        return metadata["sample_text"]["styles"]

    if "languages" in metadata and metadata["languages"]:
        for lang_code in metadata["languages"]:
            if lang_code in gflanguages and gflanguages[lang_code].sample_text.styles:
                return gflanguages[lang_code].sample_text.styles

    if "primary_script" in metadata:
        target_script = metadata["primary_script"]

        script_languages = [
            lang
            for lang in gflanguages.values()
            if lang.script == target_script and lang.sample_text.styles
        ]

        if script_languages:
            most_popular = max(script_languages, key=lambda l: l.population)
            return most_popular.sample_text.styles

    return "The quick brown fox jumps over the lazy dog."


# for some font files, setting the family name isn't working for preview.
def get_preview_family_name(ttf_path: Path):
    with TTFont(ttf_path, lazy=True) as font:
        return font["name"].getBestFullName()


def parse_metadata(metadata_path: Path):
    metadata = load_metadata(metadata_path)

    family_dir = metadata_path.parent

    font_files = metadata["fonts"]

    preview_string = get_best_preview_string(metadata)

    sample_file = next(
        (
            item["filename"]
            for item in font_files
            if item["style"] == "normal" and item["weight"] == 400
        ),
        font_files[-1]["filename"],  # get the boldest as the fallback
    )

    sample_file_path = family_dir / sample_file

    metadata = {
        "family_name": metadata["display_name"]
        if "display_name" in metadata
        else metadata["name"],
        "designer": metadata["designer"],
        "license": metadata["license"],
        "category": metadata["category"],
        "subsets": metadata["subsets"],
        "font_files": [
            f"{FONT_FILE_BASE_URL}/{family_dir.parent.name}/{family_dir.name}/{font['filename']}"
            for font in font_files
        ],
        "preview_family": get_preview_family_name(sample_file_path),
        "preview_string": preview_string,
    }

    return metadata, sample_file_path, preview_string


def main(gfonts_path: Path):
    metadatas = []
    preview_samples = []

    metadatas_total = 0

    for folder in LICENSE_FOLDERS:
        license_path = gfonts_path / folder

        if not license_path.exists():
            continue

        for metadata_path in license_path.glob("*/METADATA.pb"):
            metadatas_total += 1

            try:
                family_data, sample_file_path, preview_string = parse_metadata(
                    metadata_path
                )
                metadatas.append(family_data)
                preview_samples.append((sample_file_path, preview_string))

            except Exception as e:
                print(f"Skipping metadata extraction {metadata_path}: {e}")
                continue

    metadatas.sort(key=lambda f: f["family_name"].lower())

    Path(OUTPUT_JSON_PATH).write_text(
        json.dumps(metadatas, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    ttc_count = generate_preview_subsets_ttc_parallel(
        preview_samples,
        Path(OUTPUT_TTC_PATH),
    )

    print(
        f"\nDone! Indexed {len(metadatas)} out of {metadatas_total} families. {OUTPUT_TTC_PATH} includes {ttc_count or 0} fonts subset."
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
