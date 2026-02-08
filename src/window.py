import asyncio

from gi.repository import Adw, Gtk

from .fonts_manager import FontsManager
from .fonts_view import FontsView


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    main_stack: Adw.ViewStack = Gtk.Template.Child()
    fonts_view: FontsView = Gtk.Template.Child()
    search_button: Gtk.ToggleButton = Gtk.Template.Child()
    filter_button: Gtk.MenuButton = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        asyncio.create_task(self.setup_async())

    async def setup_async(self):
        fonts_manager = await asyncio.to_thread(FontsManager)
        self.fonts_view.set_fonts_manager(fonts_manager)
        self.main_stack.set_visible_child_name("fonts_view")
        self.search_bar.set_sensitive(True)
        self.search_button.set_sensitive(True)
        self.filter_button.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_search_changed(self, search_entry: Gtk.SearchEntry):
        self.fonts_view.search_query = search_entry.get_text()
        if self.fonts_view.selection_model.get_n_items() > 0:
            if self.main_stack.get_visible_child_name() != "fonts_view":
                self.main_stack.set_visible_child_name("fonts_view")
            self.fonts_view.list_view.scroll_to(0, Gtk.ListScrollFlags.NONE, None)
        else:
            self.main_stack.set_visible_child_name("search_empty")
