# https://googlefonts.github.io/gf-guide/metadata.html

import uuid
import json
import argparse
import uharfbuzz as hb
from pathlib import Path
from typing import List, Tuple, Dict, Any
from fontTools.ttLib import TTFont, TTCollection
from google.protobuf import text_format
from gftools import fonts_public_pb2
from google.protobuf.json_format import MessageToDict
from gflanguages import LoadLanguages, LoadScripts
from io import BytesIO


LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_TTC_PATH = "previews.ttc"

# https://github.com/googlefonts/lang
gflanguages = LoadLanguages()
gfscripts = LoadScripts()
SCRIPT_NAME_TO_ID = {script.name: code for code, script in gfscripts.items()}


def get_required_glyph_ids(face: hb.Face, text: str) -> set:
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return {info.codepoint for info in buf.glyph_infos}


def generate_subset(ttf_path: Path, preview_string: str) -> BytesIO:
    blob = hb.Blob.from_file_path(str(ttf_path))
    face = hb.Face(blob)

    # we need to add the glyph ids as well for proper preview of complex non latin languages
    gids = get_required_glyph_ids(face, preview_string)

    if 0 in gids:
        # 0 = missing character
        # For some fonts, this could be solved by generating better preview string or removing whitespaces in the preview string
        print(
            f"Some character in preview string '{preview_string}' doesn't exist in font {ttf_path}."
        )

    subset_input = hb.SubsetInput()
    for gid in gids:
        subset_input.glyph_set.add(gid)

    for char in preview_string:
        subset_input.unicode_set.add(ord(char))

    subset_face = hb.subset(face, subset_input)
    return BytesIO(subset_face.blob.data)


def generate_previews_ttc(
    preview_samples: List[Tuple[str, Path, str]],
) -> Dict[str, str]:
    subsetted_fonts = []
    preview_family_map = {}

    for id, ttf_path, preview_string in preview_samples:
        try:
            subset_data = generate_subset(ttf_path, preview_string)

            font = TTFont(subset_data)
            subsetted_fonts.append(font)

            # setting the metadata family name as font name isn't working for some fonts preview after subsetting
            # (maybe some name tables are dropped)
            preview_family_map[id] = font["name"].getBestFamilyName()
        except Exception as e:
            print(
                f"Skipping font subsetting {str(ttf_path)} for '{preview_string}': {e}"
            )
            preview_family_map[id] = None

    ttc = TTCollection()
    ttc.fonts = subsetted_fonts
    ttc.save(OUTPUT_TTC_PATH)

    return preview_family_map


def load_metadata(path: Path) -> Dict[Any, Any]:
    message = fonts_public_pb2.FamilyProto()
    text_format.Parse(path.read_text(), message, allow_unknown_field=True)
    return MessageToDict(message, preserving_proto_field_name=True)


def get_sample_by_subset_name(subset_name: str) -> str | None:
    # this is hit or miss, but works for now
    # metadatas subset field isnt one to one with iso scripts/langs
    # all available subsets can be found in pip gfsubsets
    # we could load all the fonts and find its unicode range to find script/language, but not worth it now
    # could rethink after mpv
    # a rough implementation on branch wip/list-languages
    normalized_name = subset_name.replace("-", " ").title()
    script_id = SCRIPT_NAME_TO_ID.get(normalized_name)

    if not script_id:
        return None

    script_langs = [
        l
        for l in gflanguages.values()
        if l.script == script_id and l.sample_text.tester
    ]

    if script_langs:
        most_popular = max(script_langs, key=lambda l: l.population)
        return most_popular.sample_text.tester
    return None


def get_best_preview_string(metadata) -> str:
    if "sample_text" in metadata and "tester" in metadata["sample_text"]:
        return metadata["sample_text"]["tester"]

    if "languages" in metadata and metadata["languages"]:
        for lang_code in metadata["languages"]:
            if lang_code in gflanguages and gflanguages[lang_code].sample_text.tester:
                return gflanguages[lang_code].sample_text.tester

    if "primary_script" in metadata:
        target_script = metadata["primary_script"]
        script_languages = [
            lang
            for lang in gflanguages.values()
            if lang.script == target_script and lang.sample_text.tester
        ]
        if script_languages:
            most_popular = max(script_languages, key=lambda l: l.population)
            return most_popular.sample_text.tester

    subsets = metadata.get("subsets", [])

    if "latin" in subsets or "latin-ext" in subsets:
        sample = get_sample_by_subset_name("latin")
        if sample:
            return sample

    for subset in subsets:
        if subset in ["menu", "latin", "latin-ext"]:
            continue

        sample = get_sample_by_subset_name(subset)
        if sample:
            return sample

    return "The quick brown fox jumps over the lazy dog"


def parse_metadata(metadata_path: Path) -> Tuple[Dict[str, str], Path, str]:
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
        "id": str(uuid.uuid4()),
        "family": metadata["name"],
        "display_name": metadata.get("display_name", metadata["name"]),
        "designer": metadata["designer"],
        "license": metadata["license"],
        "category": metadata["category"],
        "subsets": [s for s in metadata["subsets"] if s != "menu"],
        "files": [
            f"{FONT_FILE_BASE_URL}/{family_dir.parent.name}/{family_dir.name}/{font['filename']}"
            for font in font_files
        ],
        "preview_string": preview_string,
    }

    return metadata_out, sample_file_path, preview_string


def main(google_fonts_path: Path) -> None:
    metadatas = []
    metadatas_total = 0
    preview_samples = []

    for folder in LICENSE_FOLDERS:
        license_path = google_fonts_path / folder
        if not license_path.exists():
            continue

        for metadata_path in license_path.glob("*/METADATA.pb"):
            try:
                family_data, sample_file_path, preview_string = parse_metadata(
                    metadata_path
                )
                metadatas.append(family_data)
                preview_samples.append(
                    (family_data["id"], sample_file_path, preview_string)
                )
            except Exception as e:
                print(f"Skipping metadata extraction {str(metadata_path)}: {e}")
                continue
            finally:
                metadatas_total += 1

    preview_family_map = generate_previews_ttc(preview_samples)

    for metadata in metadatas:
        m_id = metadata["id"]
        metadata["preview_family"] = preview_family_map[m_id]

    # remove fonts where we couldn't generate a proper subset
    metadatas = [f for f in metadatas if f["preview_family"] is not None]

    metadatas.sort(key=lambda f: f["family"].lower())

    Path(OUTPUT_JSON_PATH).write_text(
        json.dumps(metadatas, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nDone! Indexed {len(metadatas)} out of {metadatas_total} families. ")


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
