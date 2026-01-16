import asyncio
import httpx
import json
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from gi.repository import GLib


class FontCategory(str, Enum):
    SANS_SERIF = "SANS_SERIF"
    DISPLAY = "DISPLAY"
    SERIF = "SERIF"
    HANDWRITING = "HANDWRITING"
    MONOSPACE = "MONOSPACE"


@dataclass
class FontFile:
    style: str
    weight: int
    filename: str
    url: str


@dataclass
class FontMetadata:
    family: str
    designer: str
    license: str
    category: FontCategory
    subsets: List[str]
    font_files: List[FontFile]
    is_variable: bool


class FontsManager:
    def __init__(self):
        self.data_dir = Path("/app/share/glyph")
        self.previews_ttc = self.data_dir / "previews.ttc"

        self.user_font_dir = Path(GLib.get_user_data_dir()) / "fonts"
        self.user_font_dir.mkdir(parents=True, exist_ok=True)

        self.fonts = [
            FontMetadata(
                font["family"],
                font["designer"],
                font["license"],
                FontCategory(font["category"]),
                font["subsets"],
                [
                    FontFile(
                        file["style"], file["weight"], file["filename"], file["url"]
                    )
                    for file in font["font_files"]
                ],
                font["is_variable"],
            )
            for font in json.loads((self.data_dir / "fonts.json").read_text())
        ]

    def get_fonts(self, category: Optional[FontCategory] = None) -> List[FontMetadata]:
        if not category:
            return self.fonts
        return [f for f in self.fonts if f.category == category]

    def get_previews_ttc(self) -> Path:
        return self.previews_ttc

    def get_category_counts(self) -> Dict[FontCategory, int]:
        counts = {}
        for font in self.fonts:
            counts[font.category] = counts.get(font.category, 0) + 1
        return counts

    async def install_font(self, font: FontMetadata):
        fonts_files = font.font_files

        async with httpx.AsyncClient() as client:
            tasks = [client.get(f.url, follow_redirects=True) for f in fonts_files]
            responses = await asyncio.gather(*tasks)

        for r in responses:
            r.raise_for_status()

        written_files: List[Path] = []

        try:
            for file, resp in zip(fonts_files, responses):
                filename = Path(file.filename)
                path = self.user_font_dir / f"{filename.stem}__glyph{filename.suffix}"

                await asyncio.to_thread(path.write_bytes, resp.content)
                written_files.append(path)
        except Exception:
            for f in written_files:
                f.unlink(missing_ok=True)

            raise
