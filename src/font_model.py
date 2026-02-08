from gi.repository import GObject


class FontModel(GObject.Object):
    __gtype_name__ = "FontModel"

    display_name = GObject.Property(type=str)
    family = GObject.Property(type=str)
    designer = GObject.Property(type=str)
    license = GObject.Property(type=str)
    is_installed = GObject.Property(type=bool, default=False)

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
    def category_label(self):
        return ", ".join([cat.replace("_", " ").title() for cat in self.category])

    @GObject.Property(type=str)
    def subsets_label(self):
        return ", ".join([sub.replace("-", " ").title() for sub in self.subsets])

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.preview_family}" size="xx-large" fallback="false">{self.preview_string}</span>'
