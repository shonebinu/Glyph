from gi.repository import Adw, GObject, Gtk

from .font_model import FontModel
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sheet-view.ui")
class SheetView(Adw.Bin):
    __gtype_name__ = "SheetView"

    font_model = GObject.Property(type=FontModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager

    @Gtk.Template.Callback()
    def on_install_clicked(self, _):
        print(self.font_model.family)
