from gi.repository import Gtk, GObject
from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/font-row.ui")
class FontRow(Gtk.Box):
    __gtype_name__ = "FontRow"

    font_model = GObject.Property(type=FontModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @Gtk.Template.Callback()
    def on_detail_clicked(self, button):
        print(f"Details for: {self.font_model.display_name}")

    @Gtk.Template.Callback()
    def on_install_clicked(self, button):
        print(f"Installing: {self.font_model.display_name}")
