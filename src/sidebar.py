from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.Bin):
    __gtype_name__ = "Sidebar"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
