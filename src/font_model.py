import os
from urllib.parse import urlparse

from gi.repository import GObject


class FontModel(GObject.Object):
    __gtype_name__ = "FontModel"

    display_name = GObject.Property(type=str)
    family = GObject.Property(type=str)
    designer = GObject.Property(type=str)
    license = GObject.Property(type=str)

    is_installed = GObject.Property(type=bool, default=False)

    is_not_installing = GObject.Property(type=bool, default=True)
    installing_state = GObject.Property(type=str)

    def __init__(self, data: dict, is_installed: bool = False):
        super().__init__()
        self.family = data["family"]
        self.display_name = data["display_name"]
        self.designer = data["designer"]
        self.license = data["license"]
        self.category = data["category"]
        self.subsets = data["subsets"]
        self.files = data["files"]
        self.preview_string = data["preview_string"]
        self.preview_family = data["preview_family"]

        self.is_installed = is_installed

        # for some reason, using _ with signals isn't working
        self.connect("notify::is-installed", lambda *_: self.notify("font-status"))

        self.is_not_installing = True
        self.installing_state = "default"

    @GObject.Property(type=str)
    def font_status(self):
        return "Installed" if self.is_installed else "Not Installed"

    @GObject.Property(type=str)
    def category_label(self):
        return ", ".join([cat.replace("_", " ").title() for cat in self.category])

    @GObject.Property(type=str)
    def subsets_label(self):
        return ", ".join([sub.replace("-", " ").title() for sub in self.subsets])

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.preview_family}" size="xx-large" fallback="false">{self.preview_string}</span>'

    @GObject.Property(type=str)
    def font_files_label(self):
        return ", ".join(
            [
                f'<a href="{fil}">{os.path.basename(urlparse(fil).path)}</a>'
                for fil in self.files
            ]
        )

    def set_installing_state(self, installing: bool):
        if installing:
            self.is_not_installing = False
            self.installing_state = "installing"
        else:
            self.is_not_installing = True
            self.installing_state = "default"
