from pathlib import Path
from typing import List
from gi.repository import Gtk, PangoCairo, GObject, Gio, Pango
from .fonts_manager import FontMetadata


class FontItem(GObject.Object):
    __gtype_name__ = "FontItem"

    def __init__(self, family, preview_family, preview_string):
        super().__init__()
        self.family = family
        self.preview_family = preview_family
        self.preview_string = preview_string


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Gtk.ScrolledWindow):
    __gtype_name__ = "FontsView"

    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.previews_font_map = PangoCairo.FontMap.new()

    def load_preview_fonts(self, file_path: Path):
        # TODO: make this async and then show loading state, after that load fonts
        # TODO: use custom symbolic icons
        # TODO: show more details dialog
        self.previews_font_map.add_font_file(str(file_path))

    def show_fonts(self, fonts: List[FontMetadata]):
        items = [
            FontItem(font.family, font.preview_family, font.preview_string)
            for font in fonts
        ]
        self.list_store.splice(0, self.list_store.get_n_items(), items)

    @Gtk.Template.Callback()
    def on_font_view_setup(self, _, list_item):
        list_item.set_selectable(False)
        list_item.set_focusable(False)
        list_item.set_activatable(False)

        main_box = Gtk.Box(
            spacing=24,
            margin_top=12,
            margin_bottom=6,
            margin_start=18,
            margin_end=24,
        )

        font_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
            hexpand=True,
        )

        family_label = Gtk.Label(halign=Gtk.Align.START)

        preview_ins = Gtk.Inscription(
            height_request=72,
            wrap_mode=Pango.WrapMode.NONE,
            text_overflow=Gtk.InscriptionOverflow.CLIP,
        )

        preview_ins.set_font_map(self.previews_font_map)

        font_box.append(family_label)
        font_box.append(preview_ins)

        install_btn = Gtk.Button(
            icon_name="folder-download-symbolic",
            css_classes=["flat"],
            valign=Gtk.Align.CENTER,
            tooltip_text="Install font",
        )

        main_box.append(font_box)
        main_box.append(install_btn)

        list_item.set_child(main_box)

        list_item.family_label = family_label
        list_item.preview_ins = preview_ins

    @Gtk.Template.Callback()
    def on_font_view_bind(self, _, list_item):
        item = list_item.get_item()

        list_item.family_label.set_text(item.family)
        list_item.preview_ins.set_markup(
            f'<span font_family="{item.preview_family}" size="x-large" fallback="false">{item.preview_string}</span>'
        )


# TODO: create custom widget font item
# pass font map to each list item, gio store
