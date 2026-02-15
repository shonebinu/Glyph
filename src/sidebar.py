from gi.repository import Adw, Gtk

from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.Bin):
    __gtype_name__ = "Sidebar"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
