import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, Adw

from .window import Window
from .preferences import Preferences, APP_ID, APP_NAME

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", lambda *_:
            Adw.AboutDialog(application_name=APP_NAME, application_icon=APP_ID,
                            developer_name="BLITZ",
                            issue_url="https://github.com/blitz2015/Cardboard/issues",
                            license_type=7,
                            release_notes="<ul><li>It just started</li></ul>",
                            release_notes_version="1.0.0",
                            version="1.0.0"
                            ).present(self.props.active_window))
        self.create_action("preferences", lambda *_: Preferences().present(self.props.active_window))
        
    def do_activate(self):
        if not self.props.active_window:
            Window(self).present()
        
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main():
    return Application().run()
