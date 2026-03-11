import asyncio
from typing import List, Set, Tuple

from gi.repository import Adw, GObject, Gtk, Pango

from .font_model import FontModel
from .fonts_manager import FontFace, FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/test-font.ui")
class TestFont(Adw.Bin):
    __gtype_name__ = "TestFont"

    font_model = GObject.Property(type=FontModel)

    test_view_stack: Adw.ViewStack = Gtk.Template.Child()
    faces_container: Gtk.Box = Gtk.Template.Child()
    preview_text_entry_row: Adw.EntryRow = Gtk.Template.Child()
    preview_size_adjustment: Gtk.Adjustment = Gtk.Template.Child()

    @GObject.Signal(arg_types=(str,))
    def show_toast(self, msg: str):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.preview_label_widgets: Set[Tuple[Gtk.Label, Pango.FontDescription]] = set()

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager

    def set_font_model(self, font_model: FontModel):
        self.test_view_stack.set_visible_child_name("loading")
        self.font_model = font_model

        self.preview_text_entry_row.set_text(font_model.preview_string)

        asyncio.create_task(self.setup_for_test())

    async def setup_for_test(self):
        try:
            (
                current_font_map,
                current_faces,
            ) = await self.fonts_manager.download_font_for_test(self.font_model)

            self.populate_faces_container(current_font_map, current_faces)
            self.refresh_preview()
            self.test_view_stack.set_visible_child_name("main_view")

        except Exception as e:
            self.emit("show-toast", str(e))

    def clear_faces_container(self):
        child = self.faces_container.get_first_child()
        while child:
            self.faces_container.remove(child)
            child = self.faces_container.get_first_child()

    def populate_faces_container(self, fontmap: Pango.FontMap, faces: List[FontFace]):
        self.clear_faces_container()

        for face in faces:
            face_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=26)

            style_label = Gtk.Label(
                label=f"{face['name']} {face['weight']}",
                halign=Gtk.Align.START,
                css_classes=["caption", "dimmed"],
            )

            preview_label = Gtk.Label(wrap=True, xalign=0)
            preview_label.set_font_map(fontmap)

            self.preview_label_widgets.add((preview_label, face["desc"]))

            face_container.append(style_label)
            face_container.append(preview_label)

            self.faces_container.append(face_container)
            self.faces_container.append(Gtk.Separator())

    @Gtk.Template.Callback()
    def refresh_preview(self, *_):
        preview_text = self.preview_text_entry_row.get_text()
        font_size = int(self.preview_size_adjustment.get_value())

        for widget, desc in self.preview_label_widgets:
            desc.set_size(Pango.SCALE * font_size)
            attr_list = Pango.AttrList()
            attr_list.insert(Pango.attr_font_desc_new(desc))

            widget.set_attributes(attr_list)
            widget.set_label(preview_text)
