from typing import List
from gi.repository import Adw, Gtk, Pango, PangoCairo
from .fonts_manager import FontsManager, FontMetadata


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    stack: Adw.ViewStack = Gtk.Template.Child()
    list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.private_font_map = PangoCairo.FontMap.new()

    def set_fonts_manager(self, fonts_manager):
        self.fonts_manager: FontsManager = fonts_manager

    def show_fonts(self, fonts: List[FontMetadata]):
        print(fonts)
