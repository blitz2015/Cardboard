from gi.repository import GLib, Gio, Adw

from .catalog import Catalog
from .entry import Entry, get_children_widgets, is_filtered
from .preferences import SETTINGS
from .danbooru import get_catalog, get_count

def filter_data(data):
    new_data = []
    for i in data:
        if not is_filtered(i):
            new_data.append(i)
    return new_data

def new_tab(self, query):
    page = self.TabView.append(Adw.Bin())
    page.Q = query
    set_query(page, query)
    return page
    
def set_query(page, query, count=False):
    if isinstance(query, dict):
        title = None
        if query["tag_string_character"] != "":
            title = f"{query['tag_string_character'].replace(' ', ', ')}"
        if query["tag_string_artist"] != "" and title != None:
            title += f" by {query['tag_string_artist']}"
        if query["tag_string_artist"] != "" and title == None:
            title = query["tag_string_artist"]
        if query["tag_string_copyright"] != "" and title == None:
            title = f"{query['tag_string_copyright'].replace(' ', ', ')}"
        if title == None:
            title = f"{query['id']}"
        GLib.idle_add(page.set_title, title)
        GLib.idle_add(page.set_keyword, query["tag_string"])
    else:
        if query == "":
            query = "Recently Uploaded"
        if count:
            query = f"{query} ({count})"
        GLib.idle_add(page.set_title, query)

def load(page, query, o=True):
    page_child = page.get_child()
    GLib.idle_add(page_child.set_child, Adw.Spinner())
    page.Q = query
    if not hasattr(page, "INDEX") or not hasattr(page, "QUERIES"):
        page.QUERIES = [query]
        page.INDEX = 0
    if o:
        page.QUERIES.append(query)
        page.INDEX = len(page.QUERIES) - 1
    if isinstance(query, dict):
        entry = Entry(query, True)
        GLib.idle_add(page_child.set_child, entry)
        set_query(page, query)
        GLib.idle_add(page_child.get_root().tab_update)
    else:
        def load_catalog(page, query):
            page_child = page.get_child()
            catalog = tab_catalog(query)
            if catalog == None:
                GLib.idle_add(page_child.set_child, Adw.StatusPage(title="No Posts Found"))
            else:
                GLib.idle_add(page_child.set_child, catalog[0])
                set_query(page, query, catalog[-1])
            try:
                GLib.idle_add(page_child.get_root().tab_update)
                return False
            except:
                return False
        page.task = Gio.Task().run_in_thread(lambda *_: load_catalog(page, query))
    return False

def tab_catalog(query):
    data = get_catalog(query)
    if data == None:
        return data
    data = filter_data(data)
    if data == []:
        return None
    children = get_children_widgets(data)
    catalog = Catalog(children)
    n = get_count(query)
    if len(children) == n:
        catalog.END = True
    if SETTINGS.get_int("posts-per-page") > len(children):
        next_page(catalog.get_child(), 3, query)
    catalog.get_child().connect("edge-reached", next_page)
    return catalog, n

def next_page(scrolledwindow, pos, query=False):
    catalog = scrolledwindow.get_parent()
    if pos == 3 and not hasattr(catalog, "END"):
        def load(query):
            if scrolledwindow.get_root() == None:
                return False
            if query:
                q = query
            else:
                q = scrolledwindow.get_root().TabView.get_selected_page().Q
            page = 2 if not hasattr(catalog, "PAGE") else catalog.PAGE + 1
            data = get_catalog(q, page)
            if data == None:
                return False
            if data == []:
                catalog.END = True
            else:
                catalog.PAGE = page
                children = get_children_widgets(filter_data(data))
                catalog.Children.extend(children)
                if not query:
                    GLib.idle_add(catalog.update_view, True)
            if SETTINGS.get_int("posts-per-page") > len(catalog.Children):
                GLib.idle_add(lambda: next_page(scrolledwindow, 3, q))
            return False
        if catalog != None:
            catalog.task = Gio.Task().run_in_thread(lambda *_: load(query))
    return False
