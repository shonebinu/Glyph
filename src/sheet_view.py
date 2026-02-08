from gi.repository import Adw, GObject, Gtk

from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sheet-view.ui")
class SheetView(Adw.Bin):
    __gtype_name__ = "SheetView"

    font_model = GObject.Property(type=FontModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
