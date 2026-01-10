import asyncio

from gi.repository import Adw, Gtk

from .fonts import Fonts


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_manager = Fonts()

        asyncio.create_task(self.populate_available_fonts())

    async def populate_available_fonts(self):
        try:
            self.available_fonts = await self.fonts_manager.fetch_available_fonts()

        except Exception as e:
            print(e)
