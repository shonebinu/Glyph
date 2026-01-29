from typing import cast
from gi.repository import Gtk, Gio, GObject
from .font_row import FontRow
from .font_model import FontModel
from .font_details_dialog import FontDetailsDialog
import asyncio
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    font_model = GObject.Property(type=Gio.ListModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.font_details_dialog = FontDetailsDialog()

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        self.custom_font_map = fonts_manager.custom_font_map
        self.font_model = fonts_manager.store

    @Gtk.Template.Callback()
    def on_factory_setup(self, _, list_item: Gtk.ListItem):
        list_item.set_activatable(False)
        list_item.set_selectable(False)
        list_item.set_focusable(False)

        row = FontRow()
        row.connect("detail-clicked", self.on_font_detail_clicked)
        row.connect("install-clicked", self.on_font_install_clicked)
        row.set_font_map(self.custom_font_map)

        list_item.set_child(row)

    @Gtk.Template.Callback()
    def on_factory_bind(self, _, list_item: Gtk.ListItem):
        row = cast(FontRow, list_item.get_child())
        model = list_item.get_item()

        row.font_model = model

    def on_font_detail_clicked(self, _, font_model: FontModel):
        self.font_details_dialog.font_model = font_model

        self.font_details_dialog.present(self.get_root())  # type: ignore

    def on_font_install_clicked(self, _, font_model: FontModel):
        asyncio.create_task(self.install_font(font_model))

    async def install_font(self, font_model: FontModel):
        await self.fonts_manager.install_font(font_model.files)
        font_model.is_installed = True
