from typing import cast
from gi.repository import Gtk, Gio, GObject
from .font_row import FontRow
from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    font_model = GObject.Property(type=Gio.ListModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @Gtk.Template.Callback()
    def on_factory_setup(self, _, list_item: Gtk.ListItem):
        list_item.set_activatable(False)
        list_item.set_selectable(False)
        list_item.set_focusable(False)

        row = FontRow()
        row.connect("detail-clicked", self.on_font_detail_clicked)
        row.connect("install-clicked", self.on_font_install_clicked)
        list_item.set_child(row)

    @Gtk.Template.Callback()
    def on_factory_bind(self, _, list_item: Gtk.ListItem):
        row = cast(FontRow, list_item.get_child())
        model = list_item.get_item()

        row.font_model = model

    def on_font_detail_clicked(self, _, font_model: FontModel):
        print(font_model.display_name)

    def on_font_install_clicked(self, _, font_model: FontModel):
        print(font_model.display_name)
