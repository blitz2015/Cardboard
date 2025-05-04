import os

from gi.repository import GLib, Gtk, Adw, Gio, Gdk, GdkPixbuf

from .danbooru import get_content

def get_media_widget(url):
    if url.endswith(("webm", "mp4")):
        file = Gio.File.new_for_uri(url) if url.startswith("https") else Gio.File.new_for_path(url)
        video = Gtk.Video(autoplay=True, file=file, height_request=200, width_request=200)
        video.get_media_stream().set_loop(True)
        return video
    picture = Gtk.Picture(height_request=200, width_request=200)
    picture.set_paintable(Adw.SpinnerPaintable(widget=picture))
    picture.task = Gio.Task().run_in_thread(lambda *_: load_picture(picture, url))
    return picture

def load_picture(picture, url):
    data = None
    if url.startswith("https"):
        data = get_content(url)
    else:
        if os.path.exists(url):
            with open(url, "rb") as f:
                data = f.read()
    if data == None:
        return False
    bytes = GLib.Bytes.new(data)
    if url.endswith("gif"):
        picture.anim = GdkPixbuf.PixbufAnimation.new_from_stream(Gio.MemoryInputStream.new_from_bytes(bytes))
        picture.iter = picture.anim.get_iter()
        def upd(*_):
            if picture.get_mapped():
                picture.iter.advance() 
                picture.set_paintable(Gdk.Texture.new_for_pixbuf(picture.iter.get_pixbuf()))
            delay_time = picture.iter.get_delay_time()
            GLib.timeout_add(20 if delay_time < 20 else delay_time, upd)
        picture.task = Gio.Task().run_in_thread(upd)
    else:
        GLib.idle_add(picture.set_paintable, Gdk.Texture.new_from_bytes(bytes))
    return False
