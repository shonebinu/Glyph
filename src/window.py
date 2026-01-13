import asyncio

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
        self.fonts_manager = FontsManager()
        self.fonts_view.set_fonts_manager(self.fonts_manager)

        self.sidebar.connect("category_selected", self.on_category_selected)
        self.sidebar.connect("search_changed", self.on_search_changed)
        self.sidebar.connect(
            "search_started", lambda *_: self.fonts_view.set_title("Search Results")
        )

        asyncio.create_task(self.setup())

    async def setup(self):
        try:
            await self.fonts_manager.fetch_fonts()

            counts = self.fonts_manager.get_category_counts()
            self.sidebar.set_category_counts(counts)

            fonts = self.fonts_manager.get_fonts()
            self.fonts_view.show_fonts(fonts)

        except Exception as e:
            # TODO: setup proper error handling for network and other errors
            # TODO: Add toasts for errors and success msgs
            # TODO: implement some network monitor that sees the network status and if came back. auto retry

            print(e)
            self.fonts_view.show_network_error_page()

    def on_category_selected(self, _, category):
        if not self.fonts_manager.is_initialized:
            return

        ctgry = FontCategory(category) if category != "ALL" else None
        fonts = self.fonts_manager.get_fonts(ctgry)
        title = (
            f"{ctgry.value.replace('_', ' ').title()} Fonts" if ctgry else "All Fonts"
        )

        self.fonts_view.set_title(title)
        self.fonts_view.show_fonts(fonts)

    def on_search_changed(self, _, search_txt):
        if not self.fonts_manager.is_initialized:
            return
        # TODO: implement search
        print(self.fonts_manager.search_fonts(search_txt))
