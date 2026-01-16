from typing import Dict
from .fonts_manager import FontCategory
from gi.repository import Adw, Gtk, GObject


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "Sidebar"

    @GObject.Signal(arg_types=(object,))
    def category_selected(self, category: FontCategory):
        pass

    @GObject.Signal(arg_types=(str,))
    def search_changed(self, query: str):
        pass

    @GObject.Signal()
    def search_started(self):
        pass

    search_button: Gtk.ToggleButton = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    sidebar_widget: Adw.Sidebar = Gtk.Template.Child()

    all_fonts_label: Adw.SidebarItem = Gtk.Template.Child()
    categories_section: Adw.SidebarSection = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sidebar_widget.connect("activated", self.on_category_selected)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_button.connect("toggled", self.on_search_button_toggled)

        self.item_to_category: Dict[Adw.SidebarItem, FontCategory] = {}

    def set_categories(self, categories: Dict[FontCategory, int]):
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        for ctgry, count in sorted_categories:
            item = Adw.SidebarItem(
                title=f"{ctgry.value.replace('_', ' ').lower().title()} Fonts",
                subtitle=f"{count} fonts",
            )
            self.item_to_category[item] = ctgry
            self.categories_section.append(item)

        self.all_fonts_label.set_subtitle(f"{sum(categories.values())} fonts")

    def on_category_selected(self, _, index: int):
        target = self.sidebar_widget.get_item(index)
        self.emit("category_selected", self.item_to_category.get(target, None))

        if self.search_button.get_active():
            self.search_button.set_active(False)

    def on_search_changed(self, entry: Gtk.SearchEntry):
        query = entry.get_text()
        self.emit("search_changed", query)

    def on_search_button_toggled(self, button: Gtk.ToggleButton):
        if button.get_active():
            self.emit("search_started")
            self.sidebar_widget.set_selected(Gtk.INVALID_LIST_POSITION)
        else:
            if self.sidebar_widget.get_selected() == Gtk.INVALID_LIST_POSITION:
                self.sidebar_widget.set_selected(0)
