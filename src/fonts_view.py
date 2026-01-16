from pathlib import Path
from typing import List
from gi.repository import Adw, Gtk, PangoCairo, GObject, Gio
from .fonts_manager import FontMetadata


class FontItem(GObject.Object):
    __gtype_name__ = "FontItem"

    family = GObject.Property(type=str)

    def __init__(self, family):
        super().__init__()
        self.family = family


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.private_font_map = PangoCairo.FontMap.new()

    def load_preview_fonts(self, file_path: Path):
        self.private_font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        items = [FontItem(font.family) for font in fonts]
        self.list_store.splice(0, self.list_store.get_n_items(), items)
