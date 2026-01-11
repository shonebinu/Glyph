from gi.repository import Adw, Gtk
from typing_extensions import List


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    stack: Adw.ViewStack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def show_network_error_page(self):
        self.stack.set_visible_child_name("network_error")

    def show_fonts(self, fonts: List):
        print(fonts)
        self.stack.set_visible_child_name("results")
