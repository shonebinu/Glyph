from gi.repository import Adw, Gtk
from .fonts_manager import FontsManager
from .fonts_view import FontsView
import asyncio


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    main_stack: Adw.ViewStack = Gtk.Template.Child()
    fonts_view: FontsView = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        asyncio.create_task(self.setup_async())

    async def setup_async(self):
        self.fonts_manager = await asyncio.to_thread(FontsManager)
        self.fonts_view.set_fonts_manager(self.fonts_manager)
        self.main_stack.set_visible_child_name("fonts_view")

        # TODO: implement smart search
        # TODO: implement fetch latest fonts data
        # TODO: implement filtering based on subset and categories (maybe license)
