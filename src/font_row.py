from gi.repository import GObject, Gtk, Pango

from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/font-row.ui")
class FontRow(Gtk.Box):
    __gtype_name__ = "FontRow"

    font_model = GObject.Property(type=FontModel)

    preview_inscription: Gtk.Inscription = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_inscription_font_map(self, font_map: Pango.FontMap):
        self.preview_inscription.set_font_map(font_map)
