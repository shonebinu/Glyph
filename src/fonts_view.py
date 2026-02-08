from typing import cast

from gi.repository import Adw, Gio, GObject, Gtk

from .font_model import FontModel
from .font_row import FontRow
from .fonts_manager import FontsManager
from .sheet_view import SheetView


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Adw.Bin):
    __gtype_name__ = "FontsView"

    font_store = GObject.Property(type=Gio.ListModel)

    search_query = GObject.Property(type=str)
    list_view: Gtk.ListView = Gtk.Template.Child()
    selection_model: Gtk.NoSelection = Gtk.Template.Child()
    bottom_sheet_layout: Adw.BottomSheet = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    sheet_view: SheetView = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        self.font_store = fonts_manager.font_store

    @Gtk.Template.Callback()
    def on_factory_setup(self, _, list_item: Gtk.ListItem):
        # custom FontMap for font preview inscriptions
        row = FontRow(self.fonts_manager.custom_font_map)
        list_item.set_child(row)

    @Gtk.Template.Callback()
    def on_factory_bind(self, _, list_item: Gtk.ListItem):
        row = cast(FontRow, list_item.get_child())
        model = cast(FontModel, list_item.get_item())

        row.font_model = model

    def set_search_query(self, text: str):
        # close bottomsheet while searching
        if self.bottom_sheet_layout.get_open():
            self.bottom_sheet_layout.set_open(False)
        self.search_query = text
        if self.selection_model.get_n_items() > 0:
            self.view_stack.set_visible_child_name("results")
            self.list_view.scroll_to(0, Gtk.ListScrollFlags.NONE, None)
        else:
            self.view_stack.set_visible_child_name("empty")

    @Gtk.Template.Callback()
    def on_list_item_activated(self, _, position):
        font_item = cast(FontModel, self.selection_model.get_item(position))
        self.sheet_view.font_model = font_item
        self.bottom_sheet_layout.set_open(True)
