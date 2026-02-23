import asyncio
import json
import shutil
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import anyio
import gi
import httpx
from typing_extensions import Any, Dict, List, Set, Tuple

gi.require_version("PangoFc", "1.0")
# PangoFc needs to be imported for using FontMap.config_changed method
from gi.repository import Gio, GLib, Gtk, Pango, PangoCairo, PangoFc  # type:ignore

from .filters import Filters
from .font_model import FontModel


class FontsManager:
    def __init__(self):
        self.filters = Filters()

        self.font_store = Gio.ListStore.new(FontModel)
        self.available_categories = Gtk.StringList()
        self.available_subsets = Gtk.StringList()

        self.user_font_dir = Path("~/.local/share/fonts/").expanduser()
        self.installed_fonts_json_path = (
            Path(GLib.get_user_data_dir()) / "glyph" / "installed.json"
        )
        self.installed_fonts = self.get_installed_fonts()

        self.default_font_map = PangoCairo.FontMap.get_default()
        self.custom_font_map = PangoCairo.FontMap.new()
        self.httpx_client = httpx.AsyncClient()

        data_dir = Path("/app/share/glyph")
        fonts, categories, subsets, self.family_model_map = self.prepare_font_data(
            data_dir / "fonts.json", data_dir / "previews"
        )

        self.font_store.splice(0, 0, fonts)
        self.available_categories.splice(0, 0, categories)
        self.available_subsets.splice(0, 0, subsets)

        self.user_font_dir.mkdir(parents=True, exist_ok=True)
        self.installed_fonts_json_path.parent.mkdir(parents=True, exist_ok=True)

        self.user_font_dir_monitor = Gio.File.new_for_path(
            str(self.user_font_dir)
        ).monitor_directory(Gio.FileMonitorFlags.NONE)
        self.user_font_dir_monitor.connect("changed", self.on_user_font_dir_changed)

        # To sync real-time system fonts changes with fontmap
        settings = Gtk.Settings.get_default()
        settings.connect(  # type: ignore
            "notify::gtk-fontconfig-timestamp",
            lambda *_: self.default_font_map.config_changed(),  # type: ignore
        )

    def get_installed_fonts(self):
        try:
            raw_installed_fonts: Dict[str, str] = json.loads(
                self.installed_fonts_json_path.read_text()
            )
        except Exception:
            return {}

        # Exclude items where the installed path doesn't exist or is empty
        # Will be overwritten in the next install/remove
        return {
            family: dir_name
            for family, dir_name in raw_installed_fonts.items()
            if (self.user_font_dir / dir_name).is_dir()
            and any((self.user_font_dir / dir_name).iterdir())
        }

    def prepare_font_data(
        self, fonts_json_path: Path, preview_files_path: Path
    ) -> Tuple[List[FontModel], List[str], List[str], Dict[str, FontModel]]:
        raw_data = json.loads(fonts_json_path.read_text())

        failed_families = self.load_custom_fonts(
            self.custom_font_map, preview_files_path, raw_data
        )

        fonts = []
        avail_cats: Set[str] = set()
        avail_subs: Set[str] = set()
        family_model_map = {}

        for font_dict in raw_data:
            family = font_dict["family"]
            model = FontModel(
                font_dict,
                is_installed=family in self.installed_fonts,
                is_preview_font_added=family not in failed_families,
            )

            fonts.append(model)
            avail_cats.update(font_dict.get("category", []))
            avail_subs.update(font_dict.get("subsets", []))
            family_model_map[family] = model

        categories = ["All"] + sorted(list(avail_cats))
        subsets = ["All"] + sorted(list(avail_subs))

        return fonts, categories, subsets, family_model_map

    def load_custom_fonts(
        self,
        font_map: Pango.FontMap,
        preview_files_path: Path,
        font_data: List[Dict[str, Any]],
    ) -> Set[str]:
        failed_families = set()

        for font in font_data:
            family = font["family"]
            preview_family = font["preview_family"]

            preview_file = preview_files_path / f"{preview_family}.ttf"

            if not preview_file.exists():
                failed_families.add(family)
                continue

            success = font_map.add_font_file(str(preview_file))
            if not success:
                failed_families.add(family)

        return failed_families

    def sync_installed_fonts_json(self):
        self.installed_fonts_json_path.write_text(
            json.dumps(self.installed_fonts, indent=2)
        )

    def is_font_outside_installed(self, family: str) -> bool:
        return self.default_font_map.get_family(family) is not None

    async def remove_font(self, font: FontModel):
        try:
            dir_name = self.installed_fonts[font.family]

            path = self.user_font_dir / dir_name
            if path.is_dir():
                await asyncio.to_thread(shutil.rmtree, path)

            self.installed_fonts.pop(font.family)
            self.sync_installed_fonts_json()
            font.is_installed = False

        except Exception as e:
            raise Exception(f"Failed to remove font :{e}")

    async def install_font(self, font: FontModel):
        try:
            font.is_installing = True

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
                await asyncio.to_thread(
                    shutil.move, tmp_dir_path, font_destination_path
                )

            self.installed_fonts[font.family] = font_destination_path.name
            self.sync_installed_fonts_json()
            font.is_installed = True

        except httpx.RequestError:
            raise Exception(
                "Connectivity issue. Please check your internet connection."
            )
        except httpx.HTTPStatusError as e:
            raise Exception(f"Server error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Installation failed: {e}")
        finally:
            font.is_installing = False

    async def download_font_file(self, url: str, path: Path):
        async with self.httpx_client.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            async with await anyio.open_file(path, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=256 * 1024):
                    await f.write(chunk)

    def on_user_font_dir_changed(
        self,
        monitor: Gio.FileMonitor,
        file: Gio.File,
        other_file: Gio.File,
        event_type: Gio.FileMonitorEvent,
    ):
        if event_type in (
            Gio.FileMonitorEvent.DELETED,
            Gio.FileMonitorEvent.CHANGES_DONE_HINT,
        ):
            changed_dir = file.get_basename()

            family = next(
                (
                    family
                    for family, dir in self.installed_fonts.items()
                    if dir == changed_dir
                ),
                None,
            )

            if not changed_dir or not family:
                return

            changed_dir_path = self.user_font_dir / changed_dir

            if not changed_dir_path.is_dir() or not any(changed_dir_path.iterdir()):
                self.installed_fonts.pop(family)
                self.update_model_installed_status(family, False)

    def update_model_installed_status(self, family: str, is_installed: bool):
        model = self.family_model_map.get(family)

        if not model:
            return

        if model.is_installed != is_installed:
            print(model.family)
            model.is_installed = is_installed
