from gi.repository import Gtk, Gio


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    selection_model: Gtk.NoSelection = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_model(self, model: Gio.ListModel):
        self.selection_model.set_model(model)
        # TODO: make this and json loading async and then show loading state, after that load fonts
        # TODO: use custom symbolic icons
        # TODO: show more details dialog
