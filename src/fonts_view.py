from typing import cast
from gi.repository import Gtk, Gio, GObject, Adw
from .font_row import FontRow
from .font_model import FontModel
from .font_details_dialog import FontDetailsDialog
import asyncio
from .fonts_manager import FontsManager
import httpx


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts-view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    search_query = GObject.Property(type=str)
    list_view: Gtk.ListView = Gtk.Template.Child()
    selection_model: Gtk.NoSelection = Gtk.Template.Child()

    @GObject.Signal(arg_types=(str,))
    def installation_error(self, msg: str):
        pass

    @GObject.Signal(arg_types=(str,))
    def installation_success(self, msg: str):
        pass

    font_model = GObject.Property(type=Gio.ListModel)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.font_details_dialog = FontDetailsDialog()

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        self.custom_font_map = fonts_manager.custom_font_map
        self.font_model = fonts_manager.store
        self.set_font_map(self.custom_font_map)

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
        self.font_details_dialog.font_model = font_model

        self.font_details_dialog.present(self.get_root())  # type: ignore

    def on_font_install_clicked(self, _, font_model: FontModel):
        asyncio.create_task(self.run_font_install_process(font_model))

    async def run_font_install_process(self, font_model: FontModel):
        if font_model.is_installed:
            dialog = Adw.AlertDialog(
                heading="Reinstall Font",
                body=f"The font `{font_model.family}` already exists in the system. Do you want to install it again?",
                close_response="cancel",
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_response_appearance(
                "install", Adw.ResponseAppearance.DESTRUCTIVE
            )

            response = await dialog.choose(self.get_root(), None)  # type: ignore
            if response != "install":
                return

        try:
            font_model.set_install_status(installing=True)
            await self.fonts_manager.install_font(font_model.files)
            font_model.is_installed = True
            self.emit("installation-success", f"{font_model.family} font installed.")
        except httpx.RequestError:
            self.emit(
                "installation-error",
                "Connectivity issue. Please check your internet connection.",
            )
        except httpx.HTTPStatusError as e:
            self.emit(
                "installation-error",
                f"Error: Server responded with status {e.response.status_code}.",
            )
        except Exception:
            self.emit(
                "installation-error",
                "Error: Something went wrong while installing the font.",
            )
        finally:
            font_model.set_install_status(installing=False)
