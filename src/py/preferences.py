import os

from gi.repository import GLib, Gtk, Gio, Adw

APP_ID = "io.github.blitz2015.Cardboard"
APP_NAME = APP_ID.rsplit(".")[-1]

UI_RESOURCE = "/" + APP_ID.replace(".", "/") + "/gtk/"

SETTINGS = Gio.Settings(schema_id=APP_ID)

DATA_DIR = os.path.join(GLib.get_user_data_dir(), APP_NAME.lower())

RESTORE_JSON = os.path.join(DATA_DIR, "restore.json")
        
FAVORITES_DIR = os.path.join(DATA_DIR, "favorites")
FAVORITES_JSONS = os.path.join(FAVORITES_DIR, "jsons")
FAVORITES_POSTS = os.path.join(FAVORITES_DIR, "posts")
FAVORITES_THUMBNAILS = os.path.join(FAVORITES_DIR, "thumbnails")

os.makedirs(DATA_DIR, exist_ok=True)

@Gtk.Template(resource_path=UI_RESOURCE + "preferences.ui")
class Preferences(Adw.PreferencesDialog):
    __gtype_name__ = "Preferences"
    
    SafeMode = Gtk.Template.Child()
    DeletedPosts = Gtk.Template.Child()
    PendingPosts = Gtk.Template.Child()
    Blacklist = Gtk.Template.Child()
    AddTag = Gtk.Template.Child()
    NewTabQuery = Gtk.Template.Child()
    SaveFavorites = Gtk.Template.Child()
    PostsperPage = Gtk.Template.Child()
    ThumbnailSize = Gtk.Template.Child()
    
    def __init__(self):
        super().__init__()
        from .tags import add_tag, prompt_tag
        for Widget in ["SafeMode", "DeletedPosts", "PendingPosts", "NewTabQuery", "SaveFavorites", "PostsperPage", "ThumbnailSize"]:
            Widget = getattr(self, Widget)
            if isinstance(Widget, Adw.EntryRow):
                signal = "text"
            if isinstance(Widget, Adw.SwitchRow):
                signal = "active"
            if isinstance(Widget, Adw.ComboRow):
                signal = "selected"
            if isinstance(Widget, Adw.SpinRow):
                signal = "value"
            SETTINGS.bind(Widget.get_name(), Widget, signal, 0)
        self.AddTag.connect("clicked", prompt_tag)
        for tag in SETTINGS.get_strv("blacklist"):
            add_tag(self.Blacklist, tag, self.AddTag)
