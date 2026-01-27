from gi.repository import GObject


class FontModel(GObject.Object):
    __gtype_name__ = "FontModel"

    display_name = GObject.Property(type=str)
    is_installed = GObject.Property(type=bool, default=False)

    def __init__(self, data: dict, is_installed: bool = False):
        super().__init__()
        self.family = data["family"]
        self.display_name = data["display_name"]
        self.designer = data["designer"]
        self.license = data["license"]
        self.category = data["category"]
        self.files = data["files"]
        self.subsets = data["subsets"]
        self.preview_string = data["preview_string"]
        self.preview_family = data["preview_family"]
        self.is_installed = is_installed

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.preview_family}" size="xx-large">{self.preview_string}</span>'

    @GObject.Property(type=str)
    def category_label(self):
        return ", ".join([cat.replace("_", " ").title() for cat in self.category])
