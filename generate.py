import json
import re
from pathlib import Path
import argparse
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen


LICENSE_FOLDERS = ["ofl", "apache", "ufl"]
FONT_FILE_BASE_URL = "https://raw.githubusercontent.com/google/fonts/main"

OUTPUT_JSON_PATH = "fonts.json"
OUTPUT_PREVIEWS_FOLDER_PATH = "previews"


def generate_svg_preview(font_path: Path, text: str, output_svg_path: Path):
    try:
        font = TTFont(font_path)
        with open(font_path, "rb") as f:
            hb_font = hb.Font(hb.Face(f.read()))

        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)

        glyph_set = font.getGlyphSet()

        bounds_pen = BoundsPen(glyph_set)
        ascender = font["hhea"].ascent
        cursor_x = 0

        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            glyph = glyph_set[font.getGlyphName(info.codepoint)]
            x = cursor_x + pos.x_offset
            y = ascender + pos.y_offset
            t_pen = TransformPen(bounds_pen, (1, 0, 0, -1, x, y))
            glyph.draw(t_pen)
            cursor_x += pos.x_advance

        if bounds_pen.bounds is None:
            return False

        x_min, y_min, x_max, y_max = bounds_pen.bounds

        svg_pen = SVGPathPen(glyph_set)
        cursor_x = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            glyph = glyph_set[font.getGlyphName(info.codepoint)]

            x = cursor_x + pos.x_offset
            y = ascender + pos.y_offset

            flip_pen = TransformPen(svg_pen, (1, 0, 0, -1, x - x_min, y - y_min))

            glyph.draw(flip_pen)
            cursor_x += pos.x_advance

        view_width = x_max - x_min
        view_height = y_max - y_min

        svg = f'<svg viewBox="0 0 {view_width} {view_height}" xmlns="http://www.w3.org/2000/svg">'
        svg += f'<path d="{svg_pen.getCommands()}" /></svg>'

        output_svg_path.write_text(svg, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error: {e}")
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
        previews_folder = Path(OUTPUT_PREVIEWS_FOLDER_PATH)
        svg_filename = f"{family_dir.name}.svg"
        svg_dest = previews_folder / svg_filename

        if generate_svg_preview(font_path, family, svg_dest):
            preview_rel_path = f"{previews_folder.name}/{svg_filename}"

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
    Path(OUTPUT_PREVIEWS_FOLDER_PATH).mkdir(exist_ok=True)

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
