from gi.repository import GLib, GObject, Gtk, Pango

from .filters import Filters
from .font_model import FontModel


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/font-row.ui")
class FontRow(Gtk.Box):
    __gtype_name__ = "FontRow"

    font_model = GObject.Property(type=FontModel)

    preview_inscription: Gtk.Inscription = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_markup(self, model: FontModel, filters: Filters):
        size = filters.preview_size

        if model.is_preview_font_added:
            family = GLib.markup_escape_text(model.preview_family)
            text = GLib.markup_escape_text(model.preview_string)
            markup = f'<span font_family="{family}" font="{size}" fallback="false">{text}</span>'
        else:
            markup = f'<span font="{size}">Failed to load font preview</span>'

        self.preview_inscription.set_markup(markup)

    def bind_row_data(
        self, model: FontModel, filters: Filters, font_map: Pango.FontMap
    ):
        self.font_model = model

        if model.is_preview_font_added:
            self.preview_inscription.set_font_map(font_map)

        filters.connect(
            "notify::preview-size", lambda *_: self.update_markup(model, filters)
        )

        self.update_markup(model, filters)

    @Gtk.Template.Callback()
    def should_show_separator(
        self, _, is_app_installed: bool, is_external_installed: bool
    ) -> bool:
        return True if is_app_installed or is_external_installed else False
