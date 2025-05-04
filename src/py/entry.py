import os

from gi.repository import GLib, Gtk, Adw, Gio

from .tags import Tags, tags
from .preferences import UI_RESOURCE, SETTINGS, FAVORITES_JSONS, FAVORITES_POSTS, FAVORITES_THUMBNAILS
from .danbooru import get_content
from .media import get_media_widget, load_picture

@Gtk.Template(resource_path=UI_RESOURCE + "entry.ui")
class Entry(Adw.Bin):   
    __gtype_name__ = "Entry"
    
    Overlay = Gtk.Template.Child()
    Revealer = Gtk.Template.Child()
    Duration = Gtk.Template.Child()
    Children = Gtk.Template.Child()
    Parent = Gtk.Template.Child()
    Open = Gtk.Template.Child()
    Tags = Gtk.Template.Child()
    Favorite = Gtk.Template.Child()
    Download = Gtk.Template.Child()
    
    def __init__(self, obj, post=False):
        self.FILTERED = True
        self.post = post
        self.o = obj
        ECM = Gtk.EventControllerMotion()
        ECM.connect("enter", lambda e, *_: e.get_widget().Revealer.set_reveal_child(True))
        ECM.connect("leave", lambda e, *_: e.get_widget().Revealer.set_reveal_child(False))
        super().__init__()
        GLib.idle_add(lambda: favorite_status(self.Favorite, obj))
        self.Tags.connect("clicked", lambda b: tags(b, b.get_ancestor(Entry).o))
        self.Favorite.connect("clicked", lambda b: favorite(b, b.get_ancestor(Entry).o))
        self.add_controller(ECM)
        if post:
            self.set_margin_bottom(10)
            self.set_margin_top(10)
            self.set_margin_end(10)
            self.set_margin_start(10)
            self.set_halign(3)
            self.Download.connect("clicked", download)
            self.Download.set_visible(True)
        else:
            picture = Gtk.Picture()
            picture.set_paintable(Adw.SpinnerPaintable(widget=picture))
            self.Overlay.set_child(picture)
            self.Open.connect("clicked", lambda b: load_query(b.get_ancestor(Entry).get_root(), b.get_ancestor(Entry).o))
            self.Open.set_visible(True)
            GC = Gtk.GestureClick(button=2)
            from .tab import new_tab
            GC.connect("pressed", lambda e, *_: new_tab(e.get_widget().get_root(), e.get_widget().get_ancestor(Entry).o))
            self.add_controller(GC)
            if obj["media_asset"]["duration"] != None:
                m = obj["media_asset"]["duration"] + 1
                duration = f"{int(m // 60):02}:{round(m % 60):02}"
                self.Duration.set_label(duration)
                self.Duration.set_visible(True)
        if obj["parent_id"] != None:
            self.Parent.connect("clicked", lambda b: load_query(b.get_ancestor(Entry).get_root(), f"id:{b.get_ancestor(Entry).o['parent_id']}"))
            self.Parent.set_visible(True)
        if obj["has_children"] == True:
            self.Children.connect("clicked", lambda b: load_query(b.get_ancestor(Entry).get_root(), f"parent:{b.get_ancestor(Entry).o['id']}"))
            self.Children.set_visible(True)
    
    def update_view(self):
        if not hasattr(self, "LOADED"):
            if self.post:
                url = get_post_url(self.o)
                GLib.idle_add(self.Overlay.set_child, get_media_widget(url))
            else:
                try:
                    def load(*_):
                        url = get_thumbnail_url(self.o)
                        load_picture(self.Overlay.get_child(), url)
                    self.task = Gio.Task().run_in_thread(load)
                except:
                    url = self.o["media_asset"]["variants"][0]["url"]
                    self.task = Gio.Task().run_in_thread(lambda *_: load_picture(self.Overlay.get_child(), url))
            self.LOADED = True
        return False

def load_query(root, query):
    from .tab import new_tab, load
    if root.Stack.get_visible_child_name() != "Browse":
        root.Stack.set_visible_child_name("Browse")
        P = new_tab(root, query)
        return root.TabView.set_selected_page(P)
    else:
        load(root.TabView.get_selected_page(), query)

def download(button):
    o = button.get_root().TabView.get_selected_page().Q
    data = get_content(o["file_url"])
    if data == None:
        return button.get_ancestor(Adw.ToastOverlay).add_toast(Adw.Toast(title="Offline"))
    def result(d, r):
        f = d.save_finish(r)
        if f:
            f.replace_contents_bytes_async(GLib.Bytes.new(data), None, False, 0)
    d = Gtk.FileDialog(initial_name=f"{o['id']}.{o['file_ext']}")
    d.set_title("Save File")
    d.save(button.get_root(), None, result)

def get_post_url(obj, skip=False):
    url = obj["file_url"] if not obj["file_url"].endswith("zip") else obj["large_file_url"]
    if SETTINGS.get_boolean("save-files") and not skip and os.path.exists(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json")):
        from .favorites import download_favorite
        response = download_favorite(obj)
        if response != None:
            url = response[-1]
    return url

def get_thumbnail_url(obj, skip=False):
    size = SETTINGS.get_int("thumbnail-size")
    if size == 0:
        size = "180x180"
    elif size == 1:
        size = "360x360"
    else:
        size = "720x720"
    url = next((v["url"] for v in obj["media_asset"]["variants"] if v["type"] == size), False)
    if SETTINGS.get_boolean("save-files") and not skip and os.path.exists(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json")):
        from .favorites import download_favorite
        response = download_favorite(obj)
        if response != None:
            url = response[0]
    return url

def favorite_status(button, obj):
    if os.path.exists(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json")):
        button.set_icon_name("star-large-symbolic")
        button.set_tooltip_text("Remove Favorite")
    else:
        button.set_icon_name("star-new-symbolic")
        button.set_tooltip_text("Add Favorite")

def favorite(button, obj):
    from .favorites import remove_favorite, add_favorite
    if os.path.exists(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json")):
        remove_favorite(obj)
        message = f"{obj['id']} removed from favorites"
        favorite_status(button, obj)
    else:
        add_favorite(obj)
        message = f"{obj['id']} added to favorites"
        favorite_status(button, obj)
    print(message)
    
def is_filtered(o):
    blacklist = SETTINGS.get_strv("blacklist")
    string = f"{o['tag_string']} {o['id']} rating:{o['rating']}".lower().split()
    if blacklist != []:
        if any(i in string for i in blacklist):
            return True
    if SETTINGS.get_boolean("safe-mode") and ("rating:e" in string or "rating:q" in string):
        return True
    return False

def get_children_widgets(data):
    seen_ids = set()
    return [Entry(obj) for obj in data if obj["id"] not in seen_ids and not seen_ids.add(obj["id"])]
