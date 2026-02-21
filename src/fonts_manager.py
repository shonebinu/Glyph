import asyncio
import ctypes
import json
import shutil
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import anyio
import gi
import httpx
from typing_extensions import Set

gi.require_version("PangoFc", "1.0")
# PangoFc needs to be imported for FontMap.config_changed to work

from gi.repository import Gio, GLib, Gtk, Pango, PangoCairo, PangoFc  # type: ignore

from .filters import Filters
from .font_model import FontModel


class FontsManager:
    def __init__(self):
        self.filters = Filters()

        self.font_store = Gio.ListStore.new(FontModel)
        self.available_categories = Gtk.StringList()
        self.available_subsets = Gtk.StringList()

        data_dir = Path("/app/share/glyph")
        fonts_json_path = data_dir / "fonts.json"
        preview_files_path = data_dir / "previews"

        self.installed_fonts_json_path = (
            Path(GLib.get_user_data_dir()) / "glyph" / "installed.json"
        )

        self.httpx_client = httpx.AsyncClient()

        # do not try to use env vars or library(glib,os) dir methods here for proper working in flatpak for both dev and release
        # https://github.com/shonebinu/Glyph/?tab=readme-ov-file#development
        self.user_font_dir = Path("~/.local/share/fonts/").expanduser()

        self.default_font_map = PangoCairo.FontMap.get_default()

        all_installed_fonts = self.get_all_installed_fonts()

        try:
            # family -> directory name
            self.app_installed_fonts = {
                family: dir
                for family, dir in json.loads(
                    self.installed_fonts_json_path.read_text()
                ).items()
                # dont include families that aren't in the Pango installed list. user might have uninstalled it manually ?
                # will be overwritten(removed) in the next font install
                if family in all_installed_fonts
            }
        except Exception as e:
            print(e)
            self.app_installed_fonts = {}

        self.custom_font_map = PangoCairo.FontMap.new()
        failed_families = self.load_custom_fonts(
            self.custom_font_map, preview_files_path
        )

        fonts = []
        avail_cats = set()
        avail_subs = set()
        for font in json.loads(fonts_json_path.read_text()):
            fonts.append(
                FontModel(
                    font,
                    font["family"] in all_installed_fonts,
                    font["family"] in self.app_installed_fonts,
                    font["family"] not in failed_families,
                )
            )
            avail_cats.update(font["category"])
            avail_subs.update(font["subsets"])

        self.font_store.splice(0, 0, fonts)
        self.available_categories.splice(0, 0, ["All"] + sorted(avail_cats))
        self.available_subsets.splice(0, 0, ["All"] + sorted(avail_subs))

        # Listen to any changes in system font dirs
        # https://gitlab.gnome.org/GNOME/gnome-font-viewer/-/blob/main/src/font-model.c#L506
        settings = Gtk.Settings.get_default()
        settings.connect("notify::gtk-fontconfig-timestamp", self.on_fontconfig_changed)  # type: ignore

    def load_custom_fonts(
        self, font_map: Pango.FontMap, preview_files_path: Path
    ) -> Set[str]:
        # The easiest way would've been to use add_font_file() fn in FontMap
        # but with that, during app, if any of the fonts with same name gets deleted
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

        failed_families = set()

        for preview_file in preview_files_path.iterdir():
            path_bytes = str(preview_file).encode("utf-8")
            if not libfc.FcConfigAppFontAddFile(fc_config, path_bytes):
                failed_families.add(
                    preview_file.stem
                )  # filename is same as family name
                print(f"Failed to load preview file: {preview_file}")

        libpangoft2 = ctypes.CDLL("libpangoft2-1.0.so.0")

        libpangoft2.pango_fc_font_map_set_config.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]

        libpangoft2.pango_fc_font_map_set_config(hash(font_map), fc_config)

        libfc.FcConfigDestroy(fc_config)

        return failed_families

    def on_fontconfig_changed(self, *_):
        # This needs to be called for the font map data to sync properly
        self.default_font_map.config_changed()  # type: ignore

        installed_families = self.get_all_installed_fonts()

        for i in range(self.font_store.get_n_items()):
            font_model: FontModel = self.font_store.get_item(i)  # type:ignore

            is_now_installed = font_model.family in installed_families

            if font_model.is_installed != is_now_installed:
                font_model.is_installed = is_now_installed

            # If user deletes a font installed via app manually while app is running
            if not is_now_installed and font_model.family in self.app_installed_fonts:
                font_model.is_app_installed = is_now_installed
                self.app_installed_fonts.pop(font_model.family)

    def get_all_installed_fonts(self) -> Set[str]:
        return {f.get_name() for f in self.default_font_map.list_families()}

    async def install_font(self, font: FontModel):
        try:
            font.is_installing = True

            if not self.user_font_dir.exists():
                self.user_font_dir.mkdir(parents=True, exist_ok=True)

            if not self.installed_fonts_json_path.parent.exists():
                self.installed_fonts_json_path.parent.mkdir(parents=True, exist_ok=True)

            font_destination_path = (
                self.user_font_dir / f"{font.family}_{str(uuid.uuid4())}"
            )

            # either every font files should be installed or none
            with tempfile.TemporaryDirectory(
                dir=self.user_font_dir.parent, prefix=".font_tmp_"
            ) as tmp_dir:
                tmp_dir_path = Path(tmp_dir)

                tasks = [
                    self.download_font_file(
                        url, tmp_dir_path / PurePosixPath(urlparse(url).path).name
                    )
                    for url in font.files
                ]

                await asyncio.gather(*tasks)

                if font_destination_path.exists():
                    await asyncio.to_thread(shutil.rmtree, font_destination_path)

                # If user installing a font second time, remove the old files
                if dir_name := self.app_installed_fonts.get(font.family):
                    await asyncio.to_thread(
                        shutil.rmtree, self.user_font_dir / dir_name, ignore_errors=True
                    )

                await asyncio.to_thread(
                    shutil.move, tmp_dir_path, font_destination_path
                )

            self.app_installed_fonts[font.family] = font_destination_path.name

            self.installed_fonts_json_path.write_text(
                json.dumps(self.app_installed_fonts)
            )

            font.is_installed = True
            font.is_app_installed = True

        except httpx.RequestError:
            raise Exception(
                "Connectivity issue. Please check your internet connection."
            )
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Error: Server responded with status {e.response.status_code}."
            )
        except Exception as e:
            raise Exception(
                f"Error: Something went wrong while installing the font. {e}"
            )
        finally:
            font.is_installing = False

    async def download_font_file(self, url: str, path: Path):
        async with self.httpx_client.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            async with await anyio.open_file(path, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=256 * 1024):
                    await f.write(chunk)
