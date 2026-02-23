from pathlib import PurePosixPath
from urllib.parse import urlparse

from gi.repository import GObject


class FontModel(GObject.Object):
    __gtype_name__ = "FontModel"

    display_name = GObject.Property(type=str)
    family = GObject.Property(type=str)
    designer = GObject.Property(type=str)
    license = GObject.Property(type=str)

    is_installed = GObject.Property(type=bool, default=False)

    is_installing = GObject.Property(type=bool, default=False)

    def __init__(
        self,
        data: dict,
        is_installed: bool = False,
        is_preview_font_added: bool = False,
    ):
        super().__init__(
            family=data["family"],
            display_name=data["display_name"],
            designer=data["designer"],
            license=data["license"],
            is_installed=is_installed,
        )
        self.category = data["category"]
        self.subsets = data["subsets"]
        self.files = data["files"]
        self.preview_string = data["preview_string"]
        self.preview_family = data["preview_family"]
        self.is_preview_font_added = is_preview_font_added

        # for some reason, using _ with signals isn't working
        self.connect("notify::is-installed", lambda *_: self.notify("font-status"))

    @GObject.Property(type=str)
    def font_status(self):
        return "Installed" if self.is_installed else "Not Installed"

    @GObject.Property(type=str)
    def category_label(self):
        return ", ".join(self.category)

    @GObject.Property(type=str)
    def subsets_label(self):
        return ", ".join(self.subsets)

    @GObject.Property(type=str)
    def font_files_label(self):
        return ", ".join(
            [
                f'<a href="{fil}">{PurePosixPath(urlparse(fil).path).name}</a>'
                for fil in self.files
            ]
        )
