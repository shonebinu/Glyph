import asyncio
from enum import Enum
import tempfile
from typing import List
import httpx
import re
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
from gi.repository import GLib


class Category(str, Enum):
    SANS_SERIF = "SANS_SERIF"
    DISPLAY = "DISPLAY"
    SERIF = "SERIF"
    HANDWRITING = "HANDWRITING"
    MONOSPACE = "MONOSPACE"


@dataclass
class Font:
    family: str
    category: Category
    subsets: List[str]
    font_files: List[str]


class FontsManager:
    GFONTS_INDEX_URL = "https://raw.githubusercontent.com/shonebinu/Glyph/refs/heads/main/google_fonts_index.json"
    GFONTS_CSS_API = "https://fonts.googleapis.com/css2"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10)

        self.user_font_dir = Path(GLib.get_user_data_dir()) / "fonts"
        self.user_font_dir.mkdir(parents=True, exist_ok=True)

        self.fonts = []
        self.loaded_preview_fonts = {}

    async def fetch_fonts(self):
        response = await self.client.get(self.GFONTS_INDEX_URL)
        response.raise_for_status()

        self.fonts = [
            Font(
                family=font["family"],
                category=Category(font["category"]),
                subsets=font["subsets"],
                font_files=font["fonts"],
            )
            for font in response.json()
        ]

        return self.fonts

    async def install_font(self, family_name):
        fonts_urls = next((f.font_files for f in self.fonts if f.family == family_name))

        if not fonts_urls:
            raise ValueError(f"Font family {family_name} not found")

        tasks = [self.client.get(url) for url in fonts_urls]
        responses = await asyncio.gather(*tasks)

        for r in responses:
            r.raise_for_status()

        written_files: List[Path] = []

        try:
            for url, resp in zip(fonts_urls, responses):
                filename = Path(urlparse(url).path).name
                path = (
                    self.user_font_dir
                    / f"{Path(filename).stem}__glyph{Path(filename).suffix}"
                )
                path.write_bytes(resp.content)

                written_files.append(path)
        except Exception:
            for f in written_files:
                f.unlink(missing_ok=True)

            raise

    async def get_preview_font(self, family_name: str, text: str):
        if family_name in self.loaded_preview_fonts:
            return self.loaded_preview_fonts.get(family_name)

        css_resp = await self.client.get(
            self.GFONTS_CSS_API,
            params={"family": family_name, "text": text},
            follow_redirects=True,
        )
        css_resp.raise_for_status()

        css = css_resp.text
        urls = re.findall(r'url\(["\']?(https?://[^)"\']+)["\']?\)', css)

        if not urls:
            raise Exception("Preview font not available")

        file_resp = await self.client.get(urls[-1])
        file_resp.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_resp.content)

        self.loaded_preview_fonts[family_name] = tmp.name
        return tmp.name

    async def clean_tmp(self):
        for tmp_file in self.loaded_preview_fonts.values():
            Path(tmp_file).unlink(missing_ok=True)
        asyncio.create_task(self.client.aclose())
