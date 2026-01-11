from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.NavigationPage):
    __gtype_name__ = "Sidebar"

    all_fonts_label: Adw.SidebarItem = Gtk.Template.Child()
    sans_serif_label: Adw.SidebarItem = Gtk.Template.Child()
    display_label: Adw.SidebarItem = Gtk.Template.Child()
    serif_label: Adw.SidebarItem = Gtk.Template.Child()
    handwriting_label: Adw.SidebarItem = Gtk.Template.Child()
    monospace_label: Adw.SidebarItem = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_category_count(self, fonts_by_category):
        mapping = {
            "SANS_SERIF": self.sans_serif_label,
            "DISPLAY": self.display_label,
            "SERIF": self.serif_label,
            "HANDWRITING": self.handwriting_label,
            "MONOSPACE": self.monospace_label,
        }

        for key, widget in mapping.items():
            widget.set_subtitle(f"{len(fonts_by_category[key])} nos.")

        self.all_fonts_label.set_subtitle(
            f"{sum(len(fonts_by_category[category]) for category in fonts_by_category)} nos."
        )
