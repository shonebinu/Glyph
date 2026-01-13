import asyncio
from typing import List, Optional

from gi.repository import Adw, Gtk, Pango, PangoCairo

from .fonts_manager import Font, FontsManager


class FontListRow(Gtk.ListBoxRow):
    def __init__(self, family, preview_text, font_map):
        super().__init__()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            margin_top=6,
            margin_bottom=6,
            margin_start=12,
            margin_end=12,
        )

        family_label = Gtk.Label(
            label=family, halign=Gtk.Align.START, css_classes=["caption-heading"]
        )

        preview_label = Gtk.Label(
            label=f'<span font="{family}" size="xx-large" fallback="false">{preview_text}</span>',
            halign=Gtk.Align.START,
            use_markup=True,
            ellipsize=Pango.EllipsizeMode.END,
        )
        preview_label.set_font_map(font_map)

        box.append(family_label)
        box.append(preview_label)

        self.set_child(box)


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/fonts_view.ui")
class FontsView(Adw.NavigationPage):
    __gtype_name__ = "FontsView"

    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    stack: Adw.ViewStack = Gtk.Template.Child()
    list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.private_font_map = PangoCairo.FontMap.new()

        self.offset = 0
        self.batch_size = 12
        self.loading = False
        self.current_task: Optional[asyncio.Task] = None

        self.scrolled_window.connect("edge-reached", self.on_edge_reached)

    def set_fonts_manager(self, fonts_manager):
        self.fonts_manager: FontsManager = fonts_manager

    def show_network_error_page(self):
        self.stack.set_visible_child_name("network_error")

    def on_edge_reached(self, _, pos):
        if pos == Gtk.PositionType.BOTTOM:
            self.load_next_batch()

    def show_fonts(self, fonts: List[Font]):
        if self.current_task:
            self.current_task.cancel()

        self.fonts = fonts
        self.offset = 0
        self.list_box.remove_all()

        self.private_font_map = PangoCairo.FontMap.new()

        if not fonts:
            #  TODO: self.stack.set_visible_child_name("")
            return

        self.stack.set_visible_child_name("loading")
        self.load_next_batch()

    def load_next_batch(self):
        if self.loading or self.offset >= len(self.fonts):
            return

        self.loading = True
        self.current_task = asyncio.create_task(self.fetch_and_render())

    async def fetch_and_render(self):
        try:
            start = self.offset
            end = start + self.batch_size
            batch = self.fonts[start:end]

            tasks = [
                self.fonts_manager.get_preview_font(
                    f.family, "The quick brown fox jumps over the lazy dog."
                )
                for f in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for font_item, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Skipping {font_item.family}: {result}")
                    # TODO: don't skip, show preview failed
                    continue

                self.private_font_map.add_font_file(result)

                row = FontListRow(
                    font_item.family,
                    "The quick brown fox jumps over the lazy dog",
                    self.private_font_map,
                )
                self.list_box.append(row)

            self.offset = end

            if self.stack.get_visible_child_name() == "loading":
                self.stack.set_visible_child_name("results")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error loading batch: {e}")
        finally:
            self.loading = False
            self.current_task = None
