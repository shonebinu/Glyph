from gi.repository import Adw, Gtk
from .fonts_manager import FontsManager
from .fonts_view import FontsView
import asyncio


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    main_stack: Adw.ViewStack = Gtk.Template.Child()
    fonts_view: FontsView = Gtk.Template.Child()
    search_button: Gtk.ToggleButton = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_view.connect(
            "installation-error", self.on_toast_notification_received
        )
        self.fonts_view.connect(
            "installation-success", self.on_toast_notification_received
        )

        asyncio.create_task(self.setup_async())

    async def setup_async(self):
        self.fonts_manager = await asyncio.to_thread(FontsManager)
        self.fonts_view.set_fonts_manager(self.fonts_manager)
        self.main_stack.set_visible_child_name("fonts_view")
        self.search_bar.set_sensitive(True)
        self.search_button.set_sensitive(True)

    @Gtk.Template.Callback()
    def on_search_changed(self, search_entry: Gtk.SearchEntry):
        search_text = search_entry.get_text()
        self.fonts_view.update_search_query(search_text)

    def on_toast_notification_received(self, _, msg: str):
        self.toast_overlay.add_toast(Adw.Toast(title=msg))

    # TODO: implement smart search based on subset, author etc
    # TODO: show no search result if none
    # TODO: instead of cluttering model, use notify system or something for non data stuff
    # TODO: implement fetch latest fonts data
    # TODO: implement filtering based on subset and categories (maybe license), installed
