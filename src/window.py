import asyncio
from gi.repository import Adw, Gtk

from .fonts import Fonts
from .sidebar import Sidebar
from .fonts_view import FontsView


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    sidebar: Sidebar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_manager = Fonts()

        asyncio.create_task(self.setup())

    async def setup(self):
        self.fonts_by_category = await self.fonts_manager.fetch_fonts()
        self.sidebar.set_category_count(self.fonts_by_category)
