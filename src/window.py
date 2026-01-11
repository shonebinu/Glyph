import asyncio

from gi.repository import Adw, Gtk

from .fonts_manager import FontsManager
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

        asyncio.create_task(self.setup())

        self.connect("destroy", self.fonts_manager.cleanup)

    async def setup(self):
        try:
            self.fonts_by_category = await self.fonts_manager.fetch_fonts()
            # TODO: only pass counts?
            self.sidebar.set_category_count(self.fonts_by_category)
            self.fonts_view.show_fonts(self.fonts_by_category["SERIF"])
            # TODO: listen to sidebar change with signals? and only pass that font
        except Exception:
            self.fonts_view.show_network_error_page()
        # TODO: if they turn network back on?
        # TODO: catch network error and other error different ways
