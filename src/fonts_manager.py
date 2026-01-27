import asyncio
import httpx
import json
from pathlib import Path
from urllib.parse import urlparse
from gi.repository import GLib, PangoCairo
from .font_model import FontModel


class FontsManager:
    def __init__(self):
        self._data_dir = Path("/app/share/glyph")
        self._fonts_json_path = self._data_dir / "fonts.json"
        self.previews_ttc_path = self._data_dir / "previews.ttc"

        self.font_map = PangoCairo.FontMap.get_default()
        installed_families = {f.get_name() for f in self.font_map.list_families()}

        with self._fonts_json_path.open() as f:
            self.fonts = [
                FontModel(font, font["family"] in installed_families)
                for font in json.load(f)
            ]

    async def install_font(self, font_item: FontModel):
        font_files = font_item.files

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

        font_item.is_installed = True
