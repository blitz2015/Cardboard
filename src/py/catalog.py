import weakref

from gi.repository import GLib, Gtk, Adw

from .preferences import UI_RESOURCE, SETTINGS
from .media import get_media_widget
from .entry import get_post_url

@Gtk.Template(resource_path=UI_RESOURCE + "catalog.ui")
class Catalog(Adw.Bin):   
    __gtype_name__ = "Catalog"
    
    FlowBox = Gtk.Template.Child()

    def __init__(self, Children):
        super().__init__()
        self.Children = Children
        self.FlowBox.get_parent().get_vadjustment().connect("value-changed", lambda a, b: b().update_view(), weakref.ref(self))
        
    def update_view(self, reorder=False):
        if self.get_parent() == None:
            return False
        max_columns = 2 if self.get_parent().get_width() < 1000 else 4
        columns = 0
        for n in range(4):
            if self.FlowBox.get_child_at_index(n) == None:
                break
            columns += 1
        if max_columns != columns or reorder:
            self.FlowBox.remove_all()
            self.FlowBox.set_max_children_per_line(max_columns)
            self.FlowBox.set_min_children_per_line(max_columns)
            for column in range(max_columns):
                column = Gtk.ListBox()
                column.connect("row-activated", preview)
                self.FlowBox.append(column)
            order_children(self)
        else:
            GLib.idle_add(load_in_view, self.Children)
        return False

def order_children(self):
    i = 0
    for entry in [i for i in self.Children if i.FILTERED]:
        column = self.FlowBox.get_child_at_index(i)
        if column == None:
            i = 0
            column = self.FlowBox.get_child_at_index(i)
        previous_column = entry.get_ancestor(Gtk.ListBox)
        if not (previous_column != None and previous_column.get_parent() == column):
            if previous_column != None:
                previous_column.remove(entry.get_parent())
                entry.unparent()
            column.get_child().append(entry)
        i += 1
    GLib.timeout_add(200, load_in_view, self.Children)

def load_in_view(Children):
    not_loaded_children = [i for i in Children if not hasattr(i, "LOADED") and i.FILTERED and i.get_ancestor(Gtk.ListBox) != None]
    for entry in not_loaded_children[:30]:
        visible_start = entry.get_ancestor(Gtk.ScrolledWindow).get_vadjustment().get_value()
        visible_end = visible_start + entry.get_ancestor(Gtk.ScrolledWindow).get_parent().get_height() + 800
        y = entry.compute_bounds(entry.get_ancestor(Gtk.ListBox))[1].get_y()
        if y * 4 > visible_start and y < visible_end:
            GLib.idle_add(entry.update_view)
    return False

def preview(listbox, row):
    toolbarview = Adw.ToolbarView(extend_content_to_top_edge=True)
    toolbarview.add_top_bar(Adw.HeaderBar())
    Adw.Dialog(child=toolbarview, follows_content_size=True).present(listbox.get_root())
    toolbarview.get_parent().get_parent().set_halign(3)
    toolbarview.set_content(get_media_widget(get_post_url(row.get_child().o)))
