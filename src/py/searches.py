from gi.repository import GLib, Gio, Gtk, Adw

from .catalog import Catalog
from .preferences import SETTINGS
from .tags import prompt_tag, add_tag
from .entry import get_children_widgets, is_filtered
from .danbooru import get_catalog

class SearchTags(Adw.PreferencesDialog):
    def __init__(self):
        super().__init__(follows_content_size=True, height_request=280, title="Saved Searches")
        Preferences = Adw.PreferencesPage()
        AddTag = Gtk.Button(css_classes=["flat", "circular"], icon_name="list-add-symbolic", tooltip_text="Add Tag")
        Group = Adw.PreferencesGroup()
        WrapBox = Adw.WrapBox(child_spacing=4, line_spacing=4, margin_bottom=6, margin_top=6, margin_start=6, margin_end=6, name="saved-searches")
        for tag in SETTINGS.get_strv("saved-searches"):
            add_tag(WrapBox, tag)
        WrapBox.append(AddTag)
        AddTag.connect("clicked", prompt_tag)
        Group.add(Adw.PreferencesRow(activatable=False, child=WrapBox))
        Preferences.add(Group)
        self.add(Preferences)

def load_searches(self):
    if isinstance(self.SavedSearches.get_content(), Adw.Spinner):
        return
    self.SavedSearches.set_content(Adw.Spinner())
    tags = SETTINGS.get_strv("saved-searches")
    if tags == []:
        return self.SavedSearches.set_content(self.NoSearches)
    data = []
    print(f"Loading {SETTINGS.get_int('posts-per-page')} recent posts of", tags)
    def load(*_):
        data = []
        for tag in tags:
            tag_data = get_catalog(tag)
            if tag_data == None:
                data = None
                break
            for obj in tag_data:
                if not is_filtered(obj):
                    data.append(obj)
        if data == None or data == []:
            GLib.idle_add(self.SavedSearches.set_content, Adw.StatusPage(title="No Posts Found"))
        else:
            data.sort(key=lambda x: x["id"], reverse=True)
            children = get_children_widgets(data)
            catalog = Catalog(children)
            GLib.idle_add(self.SavedSearches.set_content, catalog)
            GLib.idle_add(self.update_view)
    Gio.Task().run_in_thread(load)
