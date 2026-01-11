import asyncio
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from gi.repository import GLib

# TODO: implement data class for api?


class FontsManager:
    # index of gfonts with download links straight to raw files on google-fonts github
    # updated every 24h with github action
    GFONTS_INDEX_URL = "https://raw.githubusercontent.com/shonebinu/Glyph/refs/heads/main/google_fonts_index.json"

    # fontsource api provides subsets of fonts since we can't download large raw files for preview
    # fontsource has all google-fonts fonts in their api, so preview can be made for all fonts in the index
    # we dont install font files to system from fontsource or google apis since they are often subsets intended for web usage
    FONTSOURCE_API = "https://api.fontsource.org/v1/fonts"

    def __init__(self):
        self.client = httpx.AsyncClient()
        self.user_font_dir = Path(GLib.get_user_data_dir()) / "fonts"
        self.user_font_dir.mkdir(parents=True, exist_ok=True)

        self.fonts = []
        self.loaded_preview_fonts = {}  # family -> ttf file

    async def _request(self, url):
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise Exception("No internet connection available.")
        except Exception as e:
            raise Exception(str(e))

    async def fetch_fonts(self):
        response = await self._request(self.GFONTS_INDEX_URL)
        fonts = response.json()

        self.fonts = fonts

        fonts_by_category = {}
        for font in fonts:
            fonts_by_category.setdefault(font["category"], []).append(font)

        return fonts_by_category

    async def install_font(self, font_family):
        font_data = next(
            (f for f in self.fonts if f.get("family") == font_family), None
        )
        if not font_data:
            raise Exception("Font data not found for the given font family")

        tasks = [self._install_font(font["url"]) for font in font_data.get("fonts", [])]
        await asyncio.gather(*tasks)

    async def _install_font(self, font_url):
        file_resp = await self._request(font_url)
        filename = Path(urlparse(font_url).path).name

        target_path = self.user_font_dir / (filename + "__glyph")
        await asyncio.to_thread(target_path.write_bytes, file_resp.content)

    async def get_preview_font(self, font_family: str):
        # https://fonts.googleapis.com/css2?family=Inter&text=QuickPreview
        # the above api provides an url to lightest font subsets for the given text but can't seem to add it to Pango for preview
        # (could work in webkitview)

        if self.loaded_preview_fonts.get(font_family):
            return self.loaded_preview_fonts.get(font_family)

        # fontsource use sluggified family name as id
        fontsource_id = font_family.replace(" ", "-").lower()

        resp = await self._request(f"{self.FONTSOURCE_API}/{fontsource_id}")
        data = resp.json()

        try:
            variants = data.get("variants", {})
            weight = "400" if "400" in variants else next(iter(variants.keys()))
            style = variants[weight].get("normal") or next(
                iter(variants[weight].values())
            )
            subset_key = data.get("defSubset", "latin")
            subset = style.get(subset_key) or next(iter(style.values()))

            # for some reason lighter woff2 fonts can't be added to Pango for font rendering
            ttf_url = subset.get("url", {}).get("ttf")
        except Exception:
            return None

        if not ttf_url:
            return None

        font_resp = await self._request(ttf_url)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ttf") as tmp:
            await asyncio.to_thread(tmp.write, font_resp.content)

        self.loaded_preview_fonts[font_family] = tmp.name
        return tmp.name

    # TODO: think abt bundling index and caching it for every 24h, also cache preview fonts maybe?
    # TODO: check to see if google quick preview subsets can be used
