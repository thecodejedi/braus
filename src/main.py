#!/usr/bin/env python3
# main.py
#
# Copyright 2020 Kavya Gokul
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from gettext import gettext as _

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, Gtk  # noqa: E402

from braus.browser_mappings import BrowserMappings  # noqa: E402
from braus.window import BrausWindow  # noqa: E402


class Application(Adw.Application):
    content_types = [
        "x-scheme-handler/http",
        "x-scheme-handler/https",
        "text/html",
        "application/x-extension-htm",
        "application/x-extension-html",
        "application/x-extension-shtml",
        "application/xhtml+xml",
        "application/x-extension-xht",
    ]

    def __init__(self, **kwargs):
        super().__init__(
            application_id='com.properlypurple.braus',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
            | Gio.ApplicationFlags.NON_UNIQUE,
            **kwargs
        )
        self.url = None
        self.settings = Gio.Settings.new("com.properlypurple.braus")
        self.browser_mappings = BrowserMappings(self.settings)

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        try:
            if args and args[0] == '--set':
                self.browser_mappings.set_browser(args[1], args[2])
                return 0
            if args and args[0] == '--clear':
                self.browser_mappings.clear()
                return 0
        except IndexError:
            print(_("Missing arguments"))
            return 1
        self.url = args[0] if args else None
        self.activate()
        return 0

    def do_startup(self):
        Adw.Application.do_startup(self)
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self.on_about)
        self.add_action(about_action)
        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', lambda *_: self.quit())
        self.add_action(quit_action)

    def do_activate(self):
        self.win = BrausWindow(self, self.url)
        self.win.present()

    def on_about(self, action, param):
        about_dialog = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name=_("Braus"),
            comments=_("A small app to choose a browser to open your links"),
            website="https://braus.properlypurple.com",
            developers=["Kavya Gokul"],
            license_type=Gtk.License.GPL_3_0,
            icon_name='applications-internet',
        )
        about_dialog.present()


def main(version):
    app = Application()
    return app.run(sys.argv)
