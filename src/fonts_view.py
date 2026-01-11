from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
