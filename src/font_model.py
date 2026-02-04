from gi.repository import GObject, Pango


class FontModel(GObject.Object):
    __gtype_name__ = "FontModel"

    family = GObject.Property(type=str)
    display_name = GObject.Property(type=str)
    designer = GObject.Property(type=str)
    license = GObject.Property(type=str)
    is_installed = GObject.Property(type=bool, default=False)
    is_installing = GObject.Property(type=bool, default=False)
    install_state_name = GObject.Property(type=str, default="not_installing")

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

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.preview_family}" size="xx-large" fallback="false">{self.preview_string}</span>'

    @GObject.Property(type=str)
    def category_label(self):
        return ", ".join([cat.replace("_", " ").title() for cat in self.category])

    @GObject.Property(type=str)
    def subsets_label(self):
        return ", ".join([sub.title() for sub in self.subsets])

    @GObject.Property(type=str)
    def font_files_label(self):
        return "\n".join([f'<a href="{fil}">{fil}</a>' for fil in self.files])

    @GObject.Property(type=str)
    def font_status(self):
        return "Installed" if self.is_installed else "Not installed"

    def set_install_status(self, installing: bool):
        if installing:
            self.is_installing = True
            self.install_state_name = "installing"
        else:
            self.is_installing = False
            self.install_state_name = "not_installing"
