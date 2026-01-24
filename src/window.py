from gi.repository import Adw, Gtk
from .fonts_manager import FontsManager
from .fonts_view import FontsView


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    fonts_view: FontsView = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_manager = FontsManager()

        self.fonts_view.load_preview_fonts(self.fonts_manager.previews_ttc_path)

        self.fonts_view.show_fonts(self.fonts_manager.fonts)
