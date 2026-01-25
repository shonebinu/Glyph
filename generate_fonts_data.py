import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict
from fontTools.ttLib import TTFont, TTCollection
from google.protobuf import text_format
from gftools import fonts_public_pb2
from google.protobuf.json_format import MessageToDict
from gflanguages import LoadLanguages

LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_TTC_PATH = "previews.ttc"

gflanguages = LoadLanguages()


def get_family_name(font_path: str) -> str:
    result = subprocess.run(
        ["fc-query", "--format=%{family},", font_path],
        capture_output=True,
        text=True,
        check=True,
    )

    family = result.stdout.strip().split(",")[0]
    return family


def generate_previews_ttc(
    preview_samples: List[Tuple[str, Path, str]],
) -> Dict[str, str]:
    subsetted_fonts = []
    family_name_map = {}

    for index, (family_name, ttf_path, preview_string) in enumerate(preview_samples):
        try:
            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
                output_temp_path = tmp.name

            subprocess.run(
                [
                    "hb-subset",
                    f"--text={preview_string}",
                    f"--output-file={output_temp_path}",
                    str(ttf_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            subsetted_fonts.append(output_temp_path)

            family_name_map[family_name] = get_family_name(output_temp_path)

            print(f"{index + 1} out of {len(preview_samples)} done subsetting")
        except Exception as e:
            print(f"Skipping font subsetting {str(ttf_path)}: {e}")

    ttc = TTCollection()
    ttc.fonts = [TTFont(path) for path in subsetted_fonts]
    ttc.save(OUTPUT_TTC_PATH)

    for file in subsetted_fonts:
        fpath = Path(file)
        if fpath.exists():
            fpath.unlink()

    return family_name_map


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

    return "The quick brown fox jumps over the lazy dog"


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
        font_files[-1]["filename"],
    )

    sample_file_path = family_dir / sample_file

    metadata_out = {
        "family_name": metadata.get("display_name", metadata["name"]),
        "designer": metadata["designer"],
        "license": metadata["license"],
        "category": metadata["category"],
        "subsets": metadata["subsets"],
        "font_files": [
            f"{FONT_FILE_BASE_URL}/{family_dir.parent.name}/{family_dir.name}/{font['filename']}"
            for font in font_files
        ],
        "preview_string": preview_string,
    }

    return metadata_out, sample_file_path, preview_string


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
                preview_samples.append(
                    (family_data["family_name"], sample_file_path, preview_string)
                )
            except Exception as e:
                print(f"Skipping metadata extraction {metadata_path}: {e}")
                continue

    metadatas.sort(key=lambda f: f["family_name"].lower())

    family_name_map = generate_previews_ttc(preview_samples)

    for metadata in metadatas:
        fn = metadata["family_name"]
        metadata["preview_family"] = family_name_map.get(fn, None)

    Path(OUTPUT_JSON_PATH).write_text(
        json.dumps(metadatas, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        f"\nDone! Indexed {len(metadatas)} out of {metadatas_total} families. "
        f"{OUTPUT_TTC_PATH} includes {len(family_name_map)} font subsets."
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
