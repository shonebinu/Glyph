import asyncio

import httpx
from gi.repository import Adw, GObject, Gtk

from .font_model import FontModel
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sheet-view.ui")
class SheetView(Adw.Bin):
    __gtype_name__ = "SheetView"

    font_model = GObject.Property(type=FontModel)

    @GObject.Signal(arg_types=(str,))
    def show_toast(self, msg: str):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager

    @Gtk.Template.Callback()
    def on_install_clicked(self, _):
        asyncio.create_task(self.install_font())

    async def install_font(self):
        if self.font_model.is_installed:
            dialog = Adw.AlertDialog(
                heading="Reinstall Font",
                body=f"The font `{self.font_model.family}` already exists in the system. Do you want to install it again?",
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

        toast_msg = ""
        self.font_model.set_installing_state(installing=True)

        try:
            self.font_model.set_installing_state(installing=True)
            await self.fonts_manager.install_font(self.font_model.files)
            self.font_model.is_installed = True
            toast_msg = f"{self.font_model.family} font installed."
        except httpx.RequestError:
            toast_msg = "Connectivity issue. Please check your internet connection."
        except httpx.HTTPStatusError as e:
            toast_msg = f"Error: Server responded with status {e.response.status_code}."
        except Exception:
            toast_msg = "Error: Something went wrong while installing the font."
        finally:
            self.font_model.set_installing_state(installing=False)
            self.emit("show-toast", toast_msg)
