import asyncio
from enum import Enum
import tempfile
from typing import Dict, List, Optional
import httpx
import re
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
from gi.repository import GLib


class FontCategory(str, Enum):
    SANS_SERIF = "SANS_SERIF"
    DISPLAY = "DISPLAY"
    SERIF = "SERIF"
    HANDWRITING = "HANDWRITING"
    MONOSPACE = "MONOSPACE"


@dataclass
class Font:
    family: str
    category: FontCategory
    subsets: List[str]
    font_files: List[str]


class FontsManager:
    GFONTS_INDEX_URL = "https://raw.githubusercontent.com/shonebinu/Glyph/refs/heads/main/google_fonts_index.json"
    GFONTS_CSS_API = "https://fonts.googleapis.com/css2"

    def __init__(self):
        self.is_initialized = False

        self.client = httpx.AsyncClient(timeout=10)

        self.user_font_dir = Path(GLib.get_user_data_dir()) / "fonts"
        self.user_font_dir.mkdir(parents=True, exist_ok=True)

        self.fonts = []

    async def fetch_fonts(self):
        response = await self.client.get(self.GFONTS_INDEX_URL)
        response.raise_for_status()

        self.fonts = [
            Font(
                family=font["family"],
                category=FontCategory(font["category"]),
                subsets=font["subsets"],
                font_files=font["fonts"],
            )
            for font in response.json()
        ]

        self.is_initialized = True

    def get_fonts(self, category: Optional[FontCategory] = None) -> List[Font]:
        if not category:
            return self.fonts
        return [f for f in self.fonts if f.category == category]

    def search_fonts(self, search_txt: str):
        # TODO
        return search_txt

    def get_category_counts(self) -> Dict[FontCategory, int]:
        counts = {cat: 0 for cat in FontCategory}
        for font in self.fonts:
            counts[font.category] += 1
        return counts

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

    async def get_preview_font(self, family_name: str, text: str) -> str:
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
        # TODO: setup tmp cleaning on app close

        return tmp.name
