from gi.repository import Adw, GObject, Gtk

from .filters import Filters
from .fonts_manager import FontsManager


@Gtk.Template(resource_path="/io/github/shonebinu/Glyph/sidebar.ui")
class Sidebar(Adw.PreferencesPage):
    __gtype_name__ = "Sidebar"

    filters = GObject.Property(type=Filters)

    category_combo: Adw.ComboRow = Gtk.Template.Child()
    subset_combo: Adw.ComboRow = Gtk.Template.Child()
    installed_switch: Adw.SwitchRow = Gtk.Template.Child()
    preview_size_adjustment: Gtk.Adjustment = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.subset_combo.set_expression(
            Gtk.ClosureExpression.new(
                GObject.TYPE_STRING,
                lambda obj: obj.get_string(),
                None,
            )
        )

    def set_fonts_manager(self, fonts_manager: FontsManager):
        self.fonts_manager = fonts_manager
        filters = fonts_manager.filters

        self.category_combo.set_model(fonts_manager.available_categories)
        self.subset_combo.set_model(fonts_manager.available_subsets)

        self.category_combo.bind_property(
            "selected-item",
            filters,
            "category",
            GObject.BindingFlags.DEFAULT,
            lambda _, obj: obj.get_string(),
        )

        self.subset_combo.bind_property(
            "selected-item",
            filters,
            "subset",
            GObject.BindingFlags.DEFAULT,
            lambda _, obj: obj.get_string(),
        )

        filters.bind_property(
            "installed_only",
            self.installed_switch,
            "active",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )

        filters.bind_property(
            "preview_size",
            self.preview_size_adjustment,
            "value",
            GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE,
        )
