from gi.repository import Adw, GObject, Gtk

from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/font-details-dialog.ui")
class FontDetailsDialog(Adw.Dialog):
    __gtype_name__ = "FontDetailsDialog"

    font_model = GObject.Property(type=FontModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
