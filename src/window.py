import asyncio

from gi.repository import Adw, Gtk

from .fonts_manager import FontsManager
from .fonts_view import FontsView


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    fonts_view: FontsView = Gtk.Template.Child()
    fonts_view_window_title: Adw.WindowTitle = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_view.sheet_view.connect("show-toast", self.on_show_toast)
        self.fonts_view.filter_model.connect("items-changed", self.on_update_font_count)

        asyncio.create_task(self.setup())

    async def setup(self):
        try:
            fonts_manager = await asyncio.to_thread(FontsManager)

            self.fonts_view.set_fonts_manager(fonts_manager)
            self.view_stack.set_visible_child_name("fonts_view")

        except Exception as e:
            self.toast_overlay.add_toast(Adw.Toast(title=str(e)))

    @Gtk.Template.Callback()
    def on_search_changed(self, search_entry: Gtk.SearchEntry):
        self.fonts_view.set_search_query(search_entry.get_text())
        # closing bottomsheet removes the focus from search entry
        if not search_entry.has_focus():
            search_entry.grab_focus()

    def on_show_toast(self, _, msg: str):
        self.toast_overlay.add_toast(Adw.Toast(title=msg))

    def on_update_font_count(self, filter_model: Gtk.FilterListModel, *_):
        self.fonts_view_window_title.set_title(f"{filter_model.get_n_items()} fonts")
