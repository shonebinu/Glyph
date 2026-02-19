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

    list_view: Gtk.ListView = Gtk.Template.Child()
    selection_model: Gtk.NoSelection = Gtk.Template.Child()
    bottom_sheet_layout: Adw.BottomSheet = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    sheet_view: SheetView = Gtk.Template.Child()
    filter_model: Gtk.FilterListModel = Gtk.Template.Child()
    custom_filter: Gtk.CustomFilter = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.filter_model.connect("items-changed", self.on_font_items_changed)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        self.font_store = fonts_manager.font_store
        self.sheet_view.set_fonts_manager(fonts_manager)

        self.custom_filter.set_filter_func(self.filter_func)
        self.fonts_manager.filters.connect("notify", self.on_filters_changed)

    def filter_func(self, item) -> bool:
        font = cast(FontModel, item)
        filters = self.fonts_manager.filters

        if filters.search_query:
            q = filters.search_query.lower()
            if q not in font.display_name.lower() and q not in font.family.lower():
                return False

        if filters.category != "All" and filters.category not in font.category:
            return False

        if filters.subset != "All" and filters.subset not in font.subsets:
            return False

        if filters.installed_only and not font.is_installed:
            return False

        return True

    def on_filters_changed(self, *_):
        self.custom_filter.changed(Gtk.FilterChange.DIFFERENT)

    @Gtk.Template.Callback()
    def on_factory_setup(self, _, list_item: Gtk.ListItem):
        row = FontRow()
        list_item.set_child(row)

    @Gtk.Template.Callback()
    def on_factory_bind(self, _, list_item: Gtk.ListItem):
        row = cast(FontRow, list_item.get_child())
        model = cast(FontModel, list_item.get_item())

        row.bind_row_data(
            model, self.fonts_manager.filters, self.fonts_manager.custom_font_map
        )

    def set_search_query(self, text: str):
        self.fonts_manager.filters.search_query = text

    def on_font_items_changed(self, *_):
        if self.bottom_sheet_layout.get_open():
            self.bottom_sheet_layout.set_open(False)
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
