import asyncio
from collections import Counter
from gi.repository import Adw, Gtk

from .fonts import Fonts


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/window.ui")
class GlyphWindow(Adw.ApplicationWindow):
    __gtype_name__ = "GlyphWindow"

    all_fonts_label: Adw.SidebarItem = Gtk.Template.Child()
    sans_serif_font_label: Adw.SidebarItem = Gtk.Template.Child()
    display_font_label: Adw.SidebarItem = Gtk.Template.Child()
    serif_font_label: Adw.SidebarItem = Gtk.Template.Child()
    handwriting_font_label: Adw.SidebarItem = Gtk.Template.Child()
    monospace_font_label: Adw.SidebarItem = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fonts_manager = Fonts()

        asyncio.create_task(self.setup())

    async def setup(self):
        available_fonts = await self.fonts_manager.fetch_available_fonts()

        counts = Counter(f["category"] for f in available_fonts)

        mapping = {
            "SANS_SERIF": self.sans_serif_font_label,
            "DISPLAY": self.display_font_label,
            "SERIF": self.serif_font_label,
            "HANDWRITING": self.handwriting_font_label,
            "MONOSPACE": self.monospace_font_label,
        }

        for key, widget in mapping.items():
            widget.set_subtitle(f"{counts[key]} nos.")

        self.all_fonts_label.set_subtitle(f"{len(available_fonts)} nos.")
