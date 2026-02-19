from gi.repository import GObject


class Filters(GObject.Object):
    category = GObject.Property(type=str, default="All")
    subset = GObject.Property(type=str, default="All")
    search_query = GObject.Property(type=str, default="")
    installed_only = GObject.Property(type=bool, default=False)
    preview_size = GObject.Property(type=int, default=19)
