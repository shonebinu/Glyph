from pathlib import Path
from typing import List
from gi.repository import Adw, Gtk, PangoCairo, GObject, Gio, Pango
from .fonts_manager import FontMetadata


class FontItem(GObject.Object):
    __gtype_name__ = "FontItem"

    def __init__(self, family):
        super().__init__()
        self.family = family

        desc = Pango.FontDescription.new()
        desc.set_family(self.family)
        desc.set_size(18 * Pango.SCALE)

        self.attrs = Pango.AttrList.new()
        self.attrs.insert(Pango.attr_font_desc_new(desc))
        self.attrs.insert(Pango.attr_fallback_new(False))


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
        main_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
            margin_top=12,
            margin_bottom=6,
            margin_start=12,
            margin_end=24,
        )

        text_column = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
            hexpand=True,
        )

        family_label = Gtk.Label(
            halign=Gtk.Align.START,
        )

        text = "The quick brown fox jumps over the lazy dog."
        preview_ins = Gtk.Inscription(
            text=text,
            height_request=72,
            nat_chars=len(text),
            nat_lines=1,
            text_overflow=Gtk.InscriptionOverflow.ELLIPSIZE_END,
        )
        # TODO: set markup instead of attrs

        text_column.append(family_label)
        text_column.append(preview_ins)

        install_btn = Gtk.Button(
            label="Install",
            valign=Gtk.Align.CENTER,
        )

        main_box.append(text_column)
        main_box.append(install_btn)

        list_item.set_child(main_box)

        list_item.family_label = family_label
        list_item.preview_ins = preview_ins
        list_item.install_btn = install_btn

    @Gtk.Template.Callback()
    def on_bind(self, _, list_item):
        item = list_item.get_item()

        list_item.family_label.set_text(item.family)
        list_item.preview_ins.set_attributes(item.attrs)
