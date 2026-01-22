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

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.family}" size="xx-large" fallback="false">The quick brown fox jumps over the lazy dog</span>'


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TODO: use a custom map
        self.font_map = PangoCairo.FontMap.get_default()

    def load_preview_fonts(self, file_path: Path):
        # TODO: make this async and then show loading state, after that load fonts
        self.font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        items = [FontItem(font.family) for font in fonts]
        self.list_store.splice(0, self.list_store.get_n_items(), items)
