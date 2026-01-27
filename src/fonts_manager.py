import asyncio
import httpx
import json
from pathlib import Path
from urllib.parse import urlparse
from gi.repository import GLib, PangoCairo, Gio
from .font_model import FontModel


class FontsManager:
    def __init__(self):
        self.store = Gio.ListStore.new(FontModel)

        data_dir = Path("/app/share/glyph")
        fonts_json_path = data_dir / "fonts.json"
        previews_ttc_path = data_dir / "previews.ttc"

        font_map = PangoCairo.FontMap.get_default()
        installed_families = {f.get_name() for f in font_map.list_families()}

        with fonts_json_path.open() as f:
            fonts = [
                FontModel(font, font["family"] in installed_families)
                for font in json.load(f)
            ]

        font_map.add_font_file(str(previews_ttc_path))
        self.store.splice(0, 0, fonts)

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
