from pathlib import Path
from typing import List
from gi.repository import Gtk, PangoCairo, GObject, Gio
from .fonts_manager import FontMetadata, FontCategory


class FontItem(GObject.Object):
    __gtype_name__ = "FontItem"

    display_name = GObject.Property(type=str)

    def __init__(
        self,
        display_name: str,
        preview_family: str,
        preview_string: str,
        category: List[FontCategory],
        is_installed: bool,
    ):
        super().__init__()
        self.display_name = display_name
        self.preview_family = preview_family
        self.preview_string = preview_string
        self.category = category
        self.is_installed = is_installed

    @GObject.Property(type=str)
    def category_label(self):
        return ", ".join([cat.replace("_", " ").title() for cat in self.category])

    @GObject.Property(type=str)
    def preview_markup(self):
        return f'<span font_family="{self.preview_family}" size="x-large" fallback="false">{self.preview_string}</span>'


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.font_map = PangoCairo.FontMap.get_default()

        families = self.font_map.list_families()
        self.installed_families = {f.get_name() for f in families}

    def load_preview_fonts(self, file_path: Path):
        # TODO: make this and json loading async and then show loading state, after that load fonts
        # TODO: use custom symbolic icons
        # TODO: show more details dialog
        self.font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        # TODO: return gio list items directly? instead of recreating
        items = [
            FontItem(
                font.display_name,
                font.preview_family,
                font.preview_string,
                font.category,
                font.family in self.installed_families,
            )
            for font in fonts
        ]
        self.list_store.splice(0, self.list_store.get_n_items(), items)
