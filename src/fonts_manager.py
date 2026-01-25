import asyncio
import httpx
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Literal
from enum import Enum
from urllib.parse import urlparse
from gi.repository import GLib


class FontCategory(str, Enum):
    SANS_SERIF = "SANS_SERIF"
    DISPLAY = "DISPLAY"
    SERIF = "SERIF"
    HANDWRITING = "HANDWRITING"
    MONOSPACE = "MONOSPACE"


@dataclass
class FontMetadata:
    id: str
    family: str
    designer: str
    license: Literal["APACHE2", "OFL", "UFL"]
    category: List[FontCategory]
    files: List[str]
    subsets: List[str]
    preview_string: str
    preview_family: str


class FontsManager:
    def __init__(self):
        self._data_dir = Path("/app/share/glyph")
        self._fonts_json_path = self._data_dir / "fonts.json"

        with self._fonts_json_path.open() as f:
            self.fonts = [FontMetadata(**font) for font in json.load(f)]

        self.previews_ttc_path = self._data_dir / "previews.ttc"

    async def install_font(self, id: str):
        font = next((font for font in self.fonts if font.id == id))

        font_files = font.files

        user_font_dir = Path(GLib.get_user_data_dir()) / "fonts"
        user_font_dir.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient() as client:
            tasks = [client.get(url, follow_redirects=True) for url in font_files]
            responses = await asyncio.gather(*tasks)

        for r in responses:
            r.raise_for_status()

        for url, resp in zip(font_files, responses):
            filename = Path(urlparse(url).path).name
            path = user_font_dir / filename

            await asyncio.to_thread(path.write_bytes, resp.content)
