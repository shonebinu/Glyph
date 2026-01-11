from gi.repository import Adw, Gtk, GObject, Gio, PangoCairo
from typing_extensions import List


class ListFontItem(GObject.Object):
    __gtype_name__ = "ListFontItem"

    family = GObject.Property(type=str)

    def __init__(self, family, install_preview_font_cb):
        super().__init__()
        self.family = family

        self.install_preview_font = install_preview_font_cb

    @GObject.Property(type=str)
    def preview_markup(self):
        self.install_preview_font(self.family)

        text = "The quick brown fox jumps over the lazy dog."
        return f'<span font="{self.family}" size="xx-large">{text}</span>'


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    stack: Adw.ViewStack = Gtk.Template.Child()
    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.installed_preview_fonts = set()
        self.private_font_map = PangoCairo.FontMap.new()

    def set_font_manager(self, font_manager):
        self.font_manager = font_manager

    def show_network_error_page(self):
        self.stack.set_visible_child_name("network_error")

    def show_fonts(self, fonts: List):
        list_font_items = [
            ListFontItem(
                font["family"], lambda family: self.install_preview_font(family)
            )
            for font in fonts
        ]
        self.list_store.splice(0, 0, list_font_items)
        self.stack.set_visible_child_name("results")

    async def install_preview_font(self, family):
        print(self.install_preview_font)
        if family not in self.installed_preview_fonts:
            file_path = await self.font_manager.get_preview_font(family)
            self.private_font_map.add_font_file(file_path)
            self.private_font_map.changed()
