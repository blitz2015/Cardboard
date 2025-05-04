from gi.repository import Gtk, Adw

from .preferences import SETTINGS

class Tags(Adw.PreferencesDialog):
    def __init__(self, obj_tags):
        Page = Adw.PreferencesPage()
        for title, tags in obj_tags.items():
            if tags != "":
                Group = Adw.PreferencesGroup(title=title, halign=1)
                WrapBox = Adw.WrapBox(child_spacing=4, line_spacing=4, margin_bottom=6, margin_top=6, margin_start=6, margin_end=6, name="Tags")
                for tag in tags.split():
                    add_tag(WrapBox, tag)
                Group.add(Adw.PreferencesRow(activatable=False, child=WrapBox))
                Page.add(Group)
        super().__init__(follows_content_size=True, width_request=550, title="Tags", css_classes=["osd"])
        self.add(Page)

def activate(self, *_):
    from .tab import new_tab, load
    if self.get_root().Stack.get_visible_child_name() != "Browse":
        self.get_root().Stack.set_visible_child_name("Browse")
        P = new_tab(self.get_root(), self.get_label())
        return self.get_root().TabView.set_selected_page(P)
    else:
        return load(self.get_root().TabView.get_selected_page(), self.get_label())
 
def prompt_tag(self):
    dialog = Adw.AlertDialog(heading="New Tag", close_response="cancel", default_response="add")
    entry_row = Adw.EntryRow(title="Name")
    group = Adw.PreferencesGroup()
    group.add(entry_row)
    dialog.set_extra_child(group)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("add", "Add")
    dialog.set_response_appearance("add", 1)
    def f():
        tag = entry_row.get_text()
        if tag:
            value = SETTINGS.get_strv(self.get_ancestor(Adw.WrapBox).get_name())
            value.append(tag)
            SETTINGS.set_strv(self.get_ancestor(Adw.WrapBox).get_name(), value)
            add_tag(self.get_ancestor(Adw.WrapBox), tag, self)
            dialog.close()
    entry_row.connect("entry-activated", lambda *_: f())
    dialog.connect("response", lambda d, r: f() if r == "add" else None)
    dialog.present(self.get_root())
    entry_row.grab_focus()
    
def remove_tag(self):
    value = SETTINGS.get_strv(self.get_ancestor(Adw.WrapBox).get_name())
    value.remove(self.get_prev_sibling().get_label())
    SETTINGS.set_strv(self.get_ancestor(Adw.WrapBox).get_name(), value)
    self.get_parent().get_parent().remove(self.get_parent())
    
def add_tag(WrapBox, tag, last_widget=False):
    if WrapBox.get_name() == "Tags":
        widget = Gtk.Button(css_classes=["pill", "tag"], label=tag)
        widget.connect("clicked", activate)
        m = Gtk.GestureClick(button=2)
        from .tab import new_tab
        m.connect("pressed", lambda e, *_: new_tab(e.get_widget().get_root(), e.get_widget().get_label()))
        widget.add_controller(m)
    else:
        widget = Gtk.Box(css_classes=["pill", "btag"])
        remove_button = Gtk.Button(icon_name="window-close-symbolic", css_classes=["flat", "circular"])
        remove_button.connect("clicked", remove_tag)
        label = Gtk.Label(label=tag)
        widget.append(label)
        widget.append(remove_button)
    WrapBox.append(widget)
    if last_widget:
        WrapBox.reorder_child_after(last_widget, widget)
        
def tags(self, obj):
    Tags({"Artist": obj["tag_string_artist"], "Character": obj["tag_string_character"],
        "Copyright": obj["tag_string_copyright"], "General": obj["tag_string_general"], 
        "Meta": obj["tag_string_meta"]}).present(self.get_root())
