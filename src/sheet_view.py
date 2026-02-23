import asyncio

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
    def get_main_actions_stack_name(self, _, is_installed: bool):
        return "install" if not is_installed else "remove"

    @Gtk.Template.Callback()
    def get_install_btn_stack_name(self, _, is_installing: bool):
        return "installing" if is_installing else "default"

    @Gtk.Template.Callback()
    def on_install_clicked(self, _):
        if self.font_model.is_installing:
            return
        asyncio.create_task(self.install_font())

    @Gtk.Template.Callback()
    def on_remove_clicked(self, _):
        asyncio.create_task(self.remove_font())

    async def install_font(self):
        if self.fonts_manager.is_font_outside_installed(self.font_model.family):
            dialog = Adw.AlertDialog(
                heading="Install Font",
                body=f"The font `{self.font_model.family}` is already installed on this computer from another source. This operation may create a duplicate.",
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
            await self.fonts_manager.install_font(self.font_model)
            self.emit("show-toast", f"{self.font_model.family} font installed.")

        except Exception as e:
            self.emit("show-toast", str(e))

    async def remove_font(self):
        try:
            await self.fonts_manager.remove_font(self.font_model)
            self.emit("show-toast", f"{self.font_model.family} font removed.")

        except Exception as e:
            self.emit("show-toast", str(e))
