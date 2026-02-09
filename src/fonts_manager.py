import asyncio
import ctypes
import json
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import httpx
from gi.repository import Gio, PangoCairo

from .font_model import FontModel


class FontsManager:
    def __init__(self):
        self.font_store = Gio.ListStore.new(FontModel)

        data_dir = Path("/app/share/glyph")
        fonts_json_path = data_dir / "fonts.json"
        previews_ttc_path = data_dir / "previews.ttc"

        installed_families = {
            f.get_name() for f in PangoCairo.FontMap.get_default().list_families()
        }

        with fonts_json_path.open() as f:
            fonts_data = json.load(f)
            fonts = [
                FontModel(font, font["family"] in installed_families)
                for font in fonts_data
            ]

        self.font_store.splice(0, 0, fonts)

        # The easiest way would've been to use add_font_file() fn in FontMap
        # but with that, during app, if any of the fonts with same name gets deleted manually
        # from system fonts or user fonts dirs, the preview of the same disappears
        # (glyph:2): Pango-WARNING **: 16:41:58.000: failed to create cairo scaled font, expect ugly output. the offending font is 'Abel 19.008'
        # (glyph:2): Pango-WARNING **: 16:41:58.000: font_face status is: file not found
        # (glyph:2): Pango-WARNING **: 16:41:58.000: scaled_font status is: file not found

        # Easiest alternative is to generate and use SVG
        # Change each preview fonts name to uuid while generating it?
        # Other option is Webkit
        libfc = ctypes.CDLL("libfontconfig.so.1")

        libfc.FcConfigCreate.restype = ctypes.c_void_p

        libfc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        libfc.FcConfigAppFontAddFile.restype = ctypes.c_int

        libfc.FcConfigDestroy.argtypes = [ctypes.c_void_p]

        fc_config = libfc.FcConfigCreate()
        path_bytes = str(previews_ttc_path).encode("utf-8")
        success = libfc.FcConfigAppFontAddFile(fc_config, path_bytes)

        if not success:
            raise Exception("Failed to load preview font files.")

        self.custom_font_map = PangoCairo.FontMap.new()

        libpangoft2 = ctypes.CDLL("libpangoft2-1.0.so.0")

        libpangoft2.pango_fc_font_map_set_config.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]

        libpangoft2.pango_fc_font_map_set_config(hash(self.custom_font_map), fc_config)

        libfc.FcConfigDestroy(fc_config)

    async def install_font(self, font_files: List[str]):
        # do not try to use env vars or library(glib,os) dir methods here for proper working in flatpak for both dev and release
        # https://github.com/shonebinu/Glyph/?tab=readme-ov-file#development
        user_font_dir = Path("~/.local/share/fonts/").expanduser()
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
