import os
import json

from gi.repository import GLib, Gio, Gtk, Adw

from .preferences import UI_RESOURCE, SETTINGS, RESTORE_JSON
from .searches import SearchTags, load_searches
from .favorites import update_items, load_favorites
from .tab import new_tab, load
from .danbooru import filter_query

@Gtk.Template(resource_path=UI_RESOURCE + "window.ui")
class Window(Adw.ApplicationWindow):
    __gtype_name__ = "Window"
    
    Stack = Gtk.Template.Child()
    TabView = Gtk.Template.Child()
    BrowseEntry = Gtk.Template.Child()
    FavoritesEntry = Gtk.Template.Child()
    NoPosts = Gtk.Template.Child()
    SavedSearches = Gtk.Template.Child()
    NoSearches = Gtk.Template.Child()
    NoFavorites = Gtk.Template.Child()
    Favorites = Gtk.Template.Child()
    
    def __init__(self, app):
        self.closed_tabs = []
        super().__init__(application=app)
        attributes = ["default-width", "default-height", "maximized"]
        for attribute in attributes:
            SETTINGS.bind(attribute, self, attribute, 0)
        self.Stack.set_visible_child_name(SETTINGS.get_string("stack"))
        create_actions(self)
        connect_widgets(self)
        
    def get_pages(self, *_):
        if os.path.exists(RESTORE_JSON):
            os.remove(RESTORE_JSON)
        if self.TabView.get_n_pages() >= 1:
            pages = self.TabView.get_pages()
            pages_array = []
            for i in range(pages.get_n_items()):
                page = pages.get_item(i)
                query = page.Q
                pages_array.append(query)
            with open(RESTORE_JSON, "w") as o:
                json.dump(pages_array, o, indent=2, sort_keys=True)
        
    def fullscreen_action(self, *_):
        if not self.is_fullscreen():
            self.fullscreen()
            self.TabView.get_parent().set_reveal_top_bars(False)
            self.SavedSearches.set_reveal_top_bars(False)
            self.Favorites.get_ancestor(Adw.ToolbarView).set_reveal_top_bars(False)
        else:
            self.unfullscreen()
            self.TabView.get_parent().set_reveal_top_bars(True)
            self.SavedSearches.set_reveal_top_bars(True)
            self.Favorites.get_ancestor(Adw.ToolbarView).set_reveal_top_bars(True)
            
    def initial_tab(self, *_):
        try:
            with open(RESTORE_JSON, "r") as f:
                tabs = json.load(f)
        except:
            tabs = []
        if tabs == []:
            page = self.create_tab()
        else:
            for query in tabs:
                page = new_tab(self, query)
        self.TabView.set_selected_page(page)
        self.tab_update()
        self.get_application().connect("shutdown", self.get_pages)
        self.TabView.connect("notify::selected-page", self.tab_update)
        
    def tab_update(self, *_):
        page = self.TabView.get_selected_page()
        if hasattr(page, "Q"):
            if isinstance(page.Q, dict):
                self.BrowseEntry.set_text(f"id:{page.Q['id']}")
            else:
                self.BrowseEntry.set_text(page.Q)
            if page.get_child().get_child() == None:
                load(page, page.Q, False)
            if self.TabView.get_realized():
                self.update_view()
    
    def update_view(self, *_):
        if self.get_application() == None:
            return
        if self.Stack.get_visible_child_name() == "Browse":
            if self.TabView.get_n_pages() >= 1:
                page = self.TabView.get_selected_page()
                back = self.get_application().lookup_action("backward")
                forward = self.get_application().lookup_action("forward")
                if hasattr(page, "INDEX") and hasattr(page, "QUERIES"):
                    back.set_enabled(page.INDEX > 0 and len(page.QUERIES) - 1 > 0)
                    forward.set_enabled(len(page.QUERIES) - 1 > page.INDEX and len(page.QUERIES) -1 != page.INDEX)
                else:
                    back.set_enabled(False)
                    forward.set_enabled(False)
                view = page.get_child().get_child()
                if hasattr(view, "update_view"):
                    GLib.idle_add(view.update_view)
            else:
                self.initial_tab()
        elif self.Stack.get_visible_child_name() == "Saved Searches":
            if hasattr(self.SavedSearches.get_content(), "update_view"):
                GLib.idle_add(self.SavedSearches.get_content().update_view)
            else:
                GLib.idle_add(load_searches, self)
        elif self.Stack.get_visible_child_name() == "Favorites":
            if hasattr(self.Favorites.get_child(), "update_view"):
                GLib.idle_add(self.Favorites.get_child().update_view)
            else:
                GLib.idle_add(load_favorites, self)
        
    def create_tab(self, *_):
        page = new_tab(self, SETTINGS.get_string("new-tab-query"))
        self.TabView.set_selected_page(page)
        return page
    
    def tab_action(self, a, *_):
        if self.Stack.get_visible_child_name() != "Browse":
            return
        if "context" in a.get_name():
            page = self.TabView.CONTEXT
            if page.get_child().get_child() == None:
                load(page, page.Q, False)
        else:
            page = self.TabView.get_selected_page()
        if "open" in a.get_name():
            url = "https://danbooru.donmai.us/posts"
            if isinstance(page.Q, dict):
                url += f"/{str(page.Q['id'])}"
            else:
                url += f"?{filter_query(page.Q)}"
            Gio.AppInfo.launch_default_for_uri(url)
        elif "close" in a.get_name():
            self.TabView.close_page(page)
            if self.TabView.get_selected_page() == None:
                self.get_pages()
                self.get_application().quit()
        elif "reload" in a.get_name():
            load(page, page.Q, False)
    
    def tab_h(self, action, *_):
        page = self.TabView.get_selected_page()
        if action.get_name() == "backward":
            if page.INDEX > 0:
                page.INDEX -= 1
        elif action.get_name() == "forward":
            if page.INDEX < len(page.QUERIES) - 1:
                page.INDEX += 1
        load(page, page.QUERIES[page.INDEX], False)
       
    def reopen_closed(self, *_):
        if self.closed_tabs == []:
            return
        query = self.closed_tabs[-1]
        self.closed_tabs.remove(query)
        self.TabView.set_selected_page(new_tab(self, query))
    
    def reload(self, *_):
        if self.Stack.get_visible_child_name() == "Browse":
            page = self.TabView.get_selected_page()
            load(page, page.Q, False)
        elif self.Stack.get_visible_child_name() == "Saved Searches":
            GLib.idle_add(load_searches, self)
        elif self.Stack.get_visible_child_name() == "Favorites":
            GLib.idle_add(load_favorites, self)
    
    def change_child(self, *_):
        SETTINGS.set_string("stack",self.Stack.get_visible_child_name())
        self.update_view()
        
def create_actions(self):
    actions = [
        ("fullscreen", self.fullscreen_action, ["F11"]),
        ("reopen-tab", self.reopen_closed, ["<primary><shift>t"]),
        ("new-tab", self.create_tab, ["<primary>t"]),
        ("close-tab", self.tab_action, ["<primary>w"]),
        ("reload", self.reload, ["<primary>r", "F5"]),
        ("open-in-browser", self.tab_action, ["<shift><primary>o"]),
        ("open-context-tab", self.tab_action),
        ("close-context-tab", self.tab_action),
        ("reload-context-tab", self.tab_action),
        ("forward", self.tab_h),
        ("backward", self.tab_h),
        ("overview", lambda *_: self.Stack.get_child_by_name("Browse").set_open(True), ["<primary>o"]),
        ("saved-searches", lambda *_: SearchTags().present(self)),
    ]
    for name, callback, *accels in actions:
        self.get_application().create_action(name, callback, *accels)
    a = Gio.SimpleAction.new_stateful("sort", GLib.VariantType.new("s"), s := GLib.Variant("s", SETTINGS.get_string("sort")))
    a.connect("activate", lambda a=a, s=s, *_: (a.set_state(s), SETTINGS.set_string("sort", str(s).strip("'"))))
    self.get_application().add_action(a)

def connect_widgets(self):
    self.get_application().connect("notify::active-window", self.update_view)
    self.connect("notify::default-width", self.update_view)
    self.connect("notify::maximized", self.update_view)
    self.Stack.connect("notify::visible-child", self.change_child)
    self.Stack.get_child_by_name("Browse").connect("create-tab", self.create_tab)
    self.TabView.connect("setup-menu", lambda v, p: setattr(v, "CONTEXT", p))
    self.TabView.connect("close-page", lambda v, p: self.closed_tabs.append(p.Q))
    self.BrowseEntry.connect("activate", lambda e, *_: load(self.TabView.get_selected_page(), e.get_text()))
    self.BrowseEntry.connect("icon-press", lambda e, *_: load(self.TabView.get_selected_page(), e.get_text()))
    self.FavoritesEntry.connect("changed", lambda *_: (update_items(self, force_sort=True)))
    settings = ["safe-mode", "pending-posts", "deleted-posts", "blacklist"]
    for name in settings:
        SETTINGS.connect(f"changed::{name}", lambda *_: self.activate_action("app.reload"))
    SETTINGS.connect("changed::sort", lambda *_: (update_items(self, force_sort=True)))
    SETTINGS.connect("changed::safe-mode", lambda *_: (update_items(self, force_sort=True)))
