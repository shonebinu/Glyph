from pathlib import Path
from typing import List
from gi.repository import Adw, Gtk, PangoCairo, GObject, Gio, Pango
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
        # TODO: make this async and then show loading state, after that load fonts
        self.private_font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        items = [FontItem(font.family) for font in fonts]
        self.list_store.splice(0, self.list_store.get_n_items(), items)

    @Gtk.Template.Callback()
    def on_setup(self, _, list_item):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )

        family_label = Gtk.Label(halign=Gtk.Align.START)
        preview_label = Gtk.Label(
            halign=Gtk.Align.START, ellipsize=Pango.EllipsizeMode.END
        )

        # TODO: apply this in list view for faster
        preview_label.set_font_map(self.private_font_map)

        box.append(family_label)
        box.append(preview_label)
        list_item.set_child(box)

    @Gtk.Template.Callback()
    def on_bind(self, _, list_item):
        item = list_item.get_item()
        box = list_item.get_child()

        family_label = box.get_first_child()
        preview_label = box.get_last_child()

        family_label.set_text(item.family)
        markup = (
            f"<span font_family='{item.family}' size='xx-large'>"
            "The quick brown fox jumps over the lazy dog."
            "</span>"
        )

        preview_label.set_markup(markup)
