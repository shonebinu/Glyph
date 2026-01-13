from typing import Dict
from .fonts_manager import FontCategory
from gi.repository import Adw, Gtk, GObject


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "Sidebar"

    @GObject.Signal(arg_types=(str,))
    def category_selected(self, category: str):
        pass

    @GObject.Signal(arg_types=(str,))
    def search_changed(self, query: str):
        pass

    search_button: Gtk.ToggleButton = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    sidebar_widget: Adw.Sidebar = Gtk.Template.Child()

    all_fonts_label: Adw.SidebarItem = Gtk.Template.Child()
    sans_serif_label: Adw.SidebarItem = Gtk.Template.Child()
    display_label: Adw.SidebarItem = Gtk.Template.Child()
    serif_label: Adw.SidebarItem = Gtk.Template.Child()
    handwriting_label: Adw.SidebarItem = Gtk.Template.Child()
    monospace_label: Adw.SidebarItem = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.items = {
            self.sans_serif_label: FontCategory.SANS_SERIF,
            self.display_label: FontCategory.DISPLAY,
            self.serif_label: FontCategory.SERIF,
            self.handwriting_label: FontCategory.HANDWRITING,
            self.monospace_label: FontCategory.MONOSPACE,
        }

        self.sidebar_widget.connect("activated", self.on_category_selected)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_button.connect("toggled", self.on_search_button_toggled)

    def set_category_counts(self, counts: Dict[FontCategory, int]):
        for label, category in self.items.items():
            label.set_subtitle(f"{counts[category]} fonts")

        self.all_fonts_label.set_subtitle(f"{sum(counts.values())} fonts")

    def on_category_selected(self, sidebar: Adw.Sidebar, index: int):
        target = sidebar.get_item(index)

        if category := self.items.get(target):
            signal = category.value
        else:
            signal = "ALL"

        self.emit("category_selected", signal)

        if self.search_button.get_active():
            self.search_button.set_active(False)

    def on_search_changed(self, entry: Gtk.SearchEntry):
        query = entry.get_text()

        self.emit("search_changed", query)

    def on_search_button_toggled(self, button: Gtk.ToggleButton):
        if button.get_active():
            self.sidebar_widget.set_selected(Gtk.INVALID_LIST_POSITION)
        else:
            if self.sidebar_widget.get_selected() == Gtk.INVALID_LIST_POSITION:
                self.sidebar_widget.set_selected(0)
