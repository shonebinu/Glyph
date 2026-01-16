from gi.repository import Adw, Gtk
from .fonts_manager import FontCategory, FontsManager
from .fonts_view import FontsView
from .sidebar import Sidebar


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    sidebar: Sidebar = Gtk.Template.Child()
    fonts_view: FontsView = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sidebar.connect("category_selected", self.on_category_selected)
        self.sidebar.connect("search_changed", self.on_search_changed)
        self.sidebar.connect(
            "search_started", lambda *_: self.fonts_view.set_title("Search Results")
        )

        self.fonts_manager = FontsManager()
        self.fonts_view.load_preview_fonts(self.fonts_manager.get_previews_ttc())

        self.sidebar.set_categories(self.fonts_manager.get_category_counts())

        self.fonts_view.set_title("All Fonts")
        self.fonts_view.show_fonts(self.fonts_manager.get_fonts())

    def on_category_selected(self, _, category: FontCategory):
        self.fonts_view.show_fonts(self.fonts_manager.get_fonts(category))
        title = (
            f"{category.value.replace('_', ' ').title()} Fonts"
            if category
            else "All Fonts"
        )
        self.fonts_view.set_title(title)

    def on_search_changed(self, _, search_txt):
        print(search_txt)
