from typing import List
from gi.repository import Gtk, Gio
from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def show_fonts(self, fonts: List[FontModel]):
        self.list_store.splice(0, self.list_store.get_n_items(), fonts)
        # TODO: make this and json loading async and then show loading state, after that load fonts
        # TODO: use custom symbolic icons
        # TODO: show more details dialog
