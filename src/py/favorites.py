import os
import json
import random

from gi.repository import GLib, Gio, Gtk, Adw

from .catalog import Catalog
from .preferences import SETTINGS, FAVORITES_JSONS, FAVORITES_POSTS, FAVORITES_THUMBNAILS
from .danbooru import get_content

def download_favorite(obj):
    from .entry import get_thumbnail_url, get_post_url
    thumbnail = get_thumbnail_url(obj, True)
    if thumbnail:
        thumbnail_path = os.path.join(FAVORITES_THUMBNAILS, f"{obj['id']}{thumbnail.rsplit('.')[-1]}")
        os.makedirs(FAVORITES_THUMBNAILS, exist_ok=True)
        if not os.path.exists(thumbnail_path):
            data = get_content(thumbnail)
            if data == None:
                return None
            with open(thumbnail_path, "wb") as f:
                f.write(data)
    post = get_post_url(obj, True)
    if post:
        post_path = os.path.join(FAVORITES_POSTS, f"{obj['id']}{post.rsplit('.')[-1]}")
        os.makedirs(FAVORITES_POSTS, exist_ok=True)
        if not os.path.exists(post_path):
            data = get_content(post)
            if data == None:
                return None
            with open(post_path, "wb") as f:
                f.write(data)
            print(obj["id"], "downloaded")
    return thumbnail_path, post_path

def add_favorite(obj):
    obj["added"] = GLib.DateTime.new_now_utc().to_unix()
    os.makedirs(FAVORITES_JSONS, exist_ok=True)
    with open(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json"), "w") as file:
        json.dump(obj, file, indent=2, sort_keys=True)

def remove_favorite(obj):
    os.makedirs(FAVORITES_POSTS, exist_ok=True)
    os.makedirs(FAVORITES_THUMBNAILS, exist_ok=True)
    file = next((i for i in os.listdir(FAVORITES_POSTS) if i.rsplit(".")[0] == str(obj["id"])), False)
    thumbnail = next((i for i in os.listdir(FAVORITES_THUMBNAILS) if i.rsplit(".")[0] == str(obj["id"])), False)
    if file:
        os.remove(os.path.join(FAVORITES_POSTS, file))
    if thumbnail:
        os.remove(os.path.join(FAVORITES_THUMBNAILS, thumbnail))
    os.remove(os.path.join(FAVORITES_JSONS, f"{obj['id']}.json"))

def sort_children(Children):
    state = SETTINGS.get_string("sort")
    if state == "last-added":
        Children.sort(key=lambda x: x.o["added"], reverse=True)
    elif state == "oldest":
        Children.sort(key=lambda x: x.o["id"])
    elif state == "newest":
        Children.sort(key=lambda x: x.o["id"], reverse=True)
    else:
        random.shuffle(Children)

def update_items(self, skip=False, force_sort=False):
    Catalog = self.Favorites.get_child()
    if hasattr(Catalog, "Children"):
        query = self.FavoritesEntry.get_text().lower().strip()
        terms = query.split()
        valid_terms = [t for t in terms if not t.strip().startswith("-")]
        invalid_terms = [t.lstrip("-") for t in terms if t.strip().startswith("-")]
        orterms = [[t for t in term.strip().split() if not t.startswith("-")] for term in query.split(" or ")]
        if (not skip and SETTINGS.get_string("sort") == "random") or force_sort:
            sort_children(Catalog.Children)
        for i in Catalog.Children:
            i.FILTERED = False
            item = f"{i.o['tag_string']} {i.o['id']} rating:{i.o['rating']}".lower().split()
            if all(t in item for t in valid_terms):
                i.FILTERED = True
            if any(all(t in item for t in sublist) for sublist in orterms) and orterms != []:
                i.FILTERED = True
            if any(t in item for t in invalid_terms) and invalid_terms != []:
                i.FILTERED = False
        if not skip:
            for ind, i in enumerate([it for it in Catalog.Children if it.FILTERED]):
                if ind > SETTINGS.get_int("posts-per-page"):
                    i.FILTERED = False
            Catalog.FlowBox.get_parent().get_vadjustment().set_value(0)
            Catalog.update_view(True)
            if isinstance(self.NoPosts.get_parent(), Gtk.Overlay):
                self.Favorites.get_parent().remove_overlay(self.NoPosts)
            if all(i.FILTERED == False for i in Catalog.Children):
                self.Favorites.get_parent().add_overlay(self.NoPosts)

def load_more(self, pos):
    Catalog = self.get_parent()
    if pos == 3:
        unfiltered = [it for it in Catalog.Children if not it.FILTERED][:]
        update_items(self.get_root(), skip=True)
        filtered = [it for it in unfiltered if it.FILTERED][:]
        for ind, i in enumerate(filtered):
            if ind > SETTINGS.get_int("posts-per-page"):
                i.FILTERED = False
        if len(filtered) >= 1:
            Catalog.update_view(True)

def load_favorites(self):
    if isinstance(self.Favorites.get_child(), Adw.Spinner):
        return
    self.Favorites.set_child(Adw.Spinner())
    children = []
    def load(*_):
        from .entry import Entry, is_filtered
        if not os.path.exists(FAVORITES_JSONS):
            os.makedirs(FAVORITES_JSONS, exist_ok=True)
        for i in os.listdir(FAVORITES_JSONS):
            with open(os.path.join(FAVORITES_JSONS, i), "r") as f:
                o = json.load(f)
            if not is_filtered(o):
                children.append(Entry(o))
        if children == []:
            GLib.idle_add(self.Favorites.set_child, self.NoFavorites)
        else:
            favorites_amount(len(children))
            catalog = Catalog(children)
            catalog.get_child().connect("edge-reached", load_more)
            GLib.idle_add(self.Favorites.set_child, catalog)
            GLib.idle_add(lambda: update_items(self, force_sort=True))
        return False
    Gio.Task().run_in_thread(load)

def favorites_amount(n):
    message = "add more favorites"
    if n == 6:
        message = "⭐⭐⭐⭐⭐⭐"
    if n > 100:
        message = ":)"
    if n > 500:
        message = "cool"
    if n > 1500:
        message = "nice"
    if n > 2500:
        message = "amazing"
    if n > 5000:
        message = "⭐⭐⭐⭐⭐"
    if n > 10000:
        message = "maybe using this too much..."
    if n > 10000:
        message = "you are me, I am you"
    if n > 25000:
        message = "this won't go well..."
    print(f"You have {n} favorites,", message)
