from typing import cast

from gi.repository import Adw, Gio, GObject, Gtk

from .font_model import FontModel
from .font_row import FontRow
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    font_store = GObject.Property(type=Gio.ListModel)

    search_query = GObject.Property(type=str)
    list_view: Gtk.ListView = Gtk.Template.Child()
    selection_model: Gtk.NoSelection = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        self.font_store = fonts_manager.font_store

    @Gtk.Template.Callback()
    def on_factory_setup(self, _, list_item: Gtk.ListItem):
        row = FontRow(self.fonts_manager.custom_font_map)
        list_item.set_child(row)

    @Gtk.Template.Callback()
    def on_factory_bind(self, _, list_item: Gtk.ListItem):
        row = cast(FontRow, list_item.get_child())
        model = cast(FontModel, list_item.get_item())

        row.font_model = model
