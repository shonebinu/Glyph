from gi.repository import Adw, Gtk
from .fonts_manager import FontsManager
from .fonts_view import FontsView
import asyncio
import time


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    fonts_view: FontsView = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(time.time())
        asyncio.create_task(self.setup())

    async def setup(self):
        self.fonts_manager = FontsManager()
        await asyncio.to_thread(self.fonts_manager.load_preview_fonts)
        self.fonts_view.set_fonts_manager(self.fonts_manager)

        # TODO: implement smart search
        # TODO: implement fetch latest fonts data
        # TODO: implement filtering based on subset and categories (maybe license)
