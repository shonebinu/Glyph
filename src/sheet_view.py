import asyncio

from gi.repository import Adw, GObject, Gtk

from .font_model import FontModel
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sheet-view.ui")
class SheetView(Adw.Bin):
    __gtype_name__ = "SheetView"

    font_model = GObject.Property(type=FontModel)

    install_btn: Gtk.Button = Gtk.Template.Child()

    @GObject.Signal(arg_types=(str,))
    def show_toast(self, msg: str):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("notify::font-model", self.on_font_model_changed)

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager

    def on_font_model_changed(self, *args):
        if self.font_model:
            self.update_button_style()
            self.font_model.connect("notify::is-installed", self.update_button_style)

    def update_button_style(self, *_):
        if self.font_model.is_installed:
            self.install_btn.remove_css_class("suggested-action")
        else:
            self.install_btn.add_css_class("suggested-action")

    @Gtk.Template.Callback()
    def get_stack_state_name(self, _, is_installing: bool):
        return "installing" if is_installing else "default"

    @Gtk.Template.Callback()
    def get_install_btn_state(self, _, is_installing: bool):
        return False if is_installing else True

    @Gtk.Template.Callback()
    def get_install_label_text(self, _, is_installed: bool):
        return "Reinstall" if is_installed else "Install"

    @Gtk.Template.Callback()
    def on_install_clicked(self, _):
        if self.font_model.is_installing:
            return
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

        try:
            await self.fonts_manager.install_font(self.font_model)
            self.emit("show-toast", f"{self.font_model.family} font installed.")

        except Exception as e:
            self.emit("show-toast", str(e))
