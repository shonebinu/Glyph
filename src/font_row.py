from gi.repository import Gtk, GObject
from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/font-row.ui")
class FontRow(Gtk.Box):
    __gtype_name__ = "FontRow"

    font_model = GObject.Property(type=FontModel)

    @GObject.Signal(arg_types=(FontModel,))
    def detail_clicked(self, font_model: FontModel):
        pass

    @GObject.Signal(arg_types=(FontModel,))
    def install_clicked(self, font_model: FontModel):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @Gtk.Template.Callback()
    def on_detail_clicked(self, _):
        self.emit("detail-clicked", self.font_model)

    @Gtk.Template.Callback()
    def on_install_clicked(self, _):
        self.emit("install-clicked", self.font_model)
