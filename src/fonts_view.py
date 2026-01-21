from pathlib import Path
from typing import List
from gi.repository import Adw, Gtk, PangoCairo, GObject, Gio, Pango
from .fonts_manager import FontMetadata


class FontItem(GObject.Object):
    __gtype_name__ = "FontItem"

    family = GObject.Property(type=str)

    def __init__(self, family):
        super().__init__()
        self.family = family

        self._attrs = None

    def get_attributes(self):
        if self._attrs is None:
            desc = Pango.FontDescription.new()
            desc.set_family(self.family)
            desc.set_size(18 * Pango.SCALE)

            self._attrs = Pango.AttrList.new()
            self._attrs.insert(Pango.attr_font_desc_new(desc))
            self._attrs.insert(Pango.attr_fallback_new(False))
        return self._attrs


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # TODO: use a custom map
        self.font_map = PangoCairo.FontMap.get_default()

    def load_preview_fonts(self, file_path: Path):
        # TODO: make this async and then show loading state, after that load fonts
        self.font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        items = [FontItem(font.family) for font in fonts]
        self.list_store.splice(0, self.list_store.get_n_items(), items)

    @Gtk.Template.Callback()
    def on_setup(self, _, list_item):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )

        family_label = Gtk.Label(halign=Gtk.Align.START, css_classes=["caption"])

        text = "The quick brown fox jumps over the lazy dog."
        preview_ins = Gtk.Inscription(
            text=text,
            height_request=60,
            nat_chars=len(text),
            nat_lines=1,
            text_overflow=Gtk.InscriptionOverflow.ELLIPSIZE_END,
            wrap_mode=Pango.WrapMode.NONE,
        )

        box.append(family_label)
        box.append(preview_ins)
        list_item.set_child(box)

        list_item.f_label = family_label
        list_item.p_ins = preview_ins

    @Gtk.Template.Callback()
    def on_bind(self, _, list_item):
        item = list_item.get_item()

        list_item.f_label.set_text(item.family)
        list_item.p_ins.set_attributes(item.get_attributes())

    @Gtk.Template.Callback()
    def on_unbind(self, _, list_item):
        list_item.p_ins.set_attributes(None)
