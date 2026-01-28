from gi.repository import Gtk, Gio, GObject
from .font_model import FontModel
from .font_row import FontRow


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    font_model = GObject.Property(type=Gio.ListModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
