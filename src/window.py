# window.py
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

from gettext import gettext as _

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango  # noqa: E402


class BrausWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BrausWindow'

    def __init__(self, app, url):
        super().__init__(title=_("Braus"), application=app)
        self.set_default_size(650, 200)
        self.browsers = []

        self.entry = Gtk.Entry()
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic"
        )
        self.entry.set_text(url or "")
        self.entry.set_width_chars(35)

        header = Adw.HeaderBar()
        header.set_title_widget(self.entry)

        menu = Gio.Menu()
        menu.append(_("About"), "app.about")
        section = Gio.Menu()
        section.append(_("Never ask to be default"), "win.never-ask")
        menu.append_section(None, section)
        menu.append(_("Quit"), "app.quit")
        options_button = Gtk.MenuButton()
        options_button.set_icon_name("preferences-system-symbolic")
        options_button.set_menu_model(menu)
        header.pack_end(options_button)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.append(header)

        self.browser_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.browser_box.set_margin_top(10)
        self.browser_box.set_margin_bottom(10)
        self.browser_box.set_margin_start(10)
        self.browser_box.set_margin_end(10)
        self.browser_box.set_spacing(10)
        self.browser_box.set_homogeneous(True)
        outer_box.append(self.browser_box)

        self.set_content(outer_box)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed, app)
        self.add_controller(key_controller)

        self.setup_actions(app)
        self.populate_browsers(app)

    def setup_actions(self, app):
        set_default = Gio.SimpleAction.new("set-default", None)
        set_default.connect("activate", self.on_set_default, app)
        self.add_action(set_default)
        never_ask = Gio.SimpleAction.new("never-ask", None)
        never_ask.connect("activate", self.on_never_ask, app)
        self.add_action(never_ask)

    def populate_browsers(self, app):
        appinfo_id = app.get_application_id() + '.desktop'

        default_browser = Gio.AppInfo.get_default_for_type(
            app.content_types[1], True
        )
        if (
            app.settings.get_boolean("ask-default")
            and (
                default_browser is None
                or default_browser.get_id() != appinfo_id
            )
        ):
            banner = Adw.Banner(
                title=_("Set Braus as your default browser")
            )
            banner.set_button_label(_("Set as Default"))
            banner.set_action_name("win.set-default")
            self.get_content().prepend(banner)

        browsers = Gio.AppInfo.get_all_for_type(app.content_types[1])
        self.browsers = [
            b for b in browsers if app.get_application_id() not in b.get_id()
        ]

        url = self.entry.get_text()
        mapped = app.browser_mappings.determine_browser(url, browsers)
        if mapped is not None:
            mapped.launch_uris([url])
            self.close()
            return

        for index, browser in enumerate(self.browsers):
            gicon = browser.get_icon()
            if gicon is not None:
                icon = Gtk.Image.new_from_gicon(gicon)
            else:
                icon = Gtk.Image.new_from_icon_name('applications-internet')
            icon.set_pixel_size(48)

            label = Gtk.Label.new(browser.get_display_name())
            label.set_max_width_chars(10)
            label.set_width_chars(10)
            label.set_wrap(True)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_justify(Gtk.Justification.CENTER)

            button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            button_box.set_spacing(6)
            button_box.append(icon)
            button_box.append(label)

            browser_btn = Gtk.Button()
            browser_btn.set_child(button_box)
            browser_btn.add_css_class("flat")
            browser_btn.set_tooltip_text(browser.get_display_name())
            browser_btn.connect(
                "clicked", self.on_browser_clicked, index, app
            )

            entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            entry_box.set_spacing(6)
            entry_box.append(browser_btn)
            if index < 10:
                hotkey_label = Gtk.Label(label=str(index + 1))
                hotkey_label.add_css_class("dim-label")
                entry_box.append(hotkey_label)

            self.browser_box.append(entry_box)

    def on_key_pressed(self, controller, keyval, keycode, state, app):
        try:
            index = int(Gdk.keyval_name(keyval)) - 1
        except ValueError:
            return False
        if 0 <= index < len(self.browsers):
            self.launch_browser(index, app)
            return True
        return False

    def on_browser_clicked(self, button, index, app):
        self.launch_browser(index, app)

    def launch_browser(self, index, app):
        browser = self.browsers[index]
        browser.launch_uris([self.entry.get_text()])
        self.close()

    def on_set_default(self, action, param, app):
        appinfo = Gio.DesktopAppInfo.new(
            app.get_application_id() + '.desktop'
        )
        if appinfo is None:
            return
        try:
            for content_type in app.content_types:
                appinfo.set_as_default_for_type(content_type)
        except GLib.Error:
            print("Could not set Braus as default browser")
        self.close()

    def on_never_ask(self, action, param, app):
        app.settings.set_boolean("ask-default", False)
        self.close()
