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
        self.set_default_size(500, 220)
        self.browsers = []
        self.launching = False
        self.banner = None

        self.entry = Gtk.Entry()
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "system-search-symbolic"
        )
        self.entry.set_text(url or "")
        self.entry.set_width_chars(35)
        self.entry.set_hexpand(True)
        self.entry.set_placeholder_text(_("URL to open"))
        self.entry.set_tooltip_text(_("URL to open"))
        self.entry.connect("activate", self.on_entry_activated, app)
        self.entry.set_can_focus(False)
        entry_click = Gtk.GestureClick()
        entry_click.connect("pressed", self.on_entry_clicked)
        self.entry.add_controller(entry_click)

        header = Adw.HeaderBar()
        header.set_title_widget(self.entry)

        menu = Gio.Menu()
        menu.append(_("About Braus"), "app.about")
        section = Gio.Menu()
        section.append(_("Never ask to be default"), "win.never-ask")
        menu.append_section(None, section)
        menu.append(_("Quit"), "app.quit")
        options_button = Gtk.MenuButton()
        options_button.set_icon_name("preferences-system-symbolic")
        options_button.set_menu_model(menu)
        options_button.set_tooltip_text(_("Main Menu"))
        header.pack_end(options_button)

        self.browser_grid = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            max_children_per_line=5,
            min_children_per_line=3,
            column_spacing=12,
            row_spacing=12,
            homogeneous=True,
        )
        self.browser_grid.set_margin_top(12)
        self.browser_grid.set_margin_bottom(12)
        self.browser_grid.set_margin_start(12)
        self.browser_grid.set_margin_end(12)

        scrolled = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
        )
        scrolled.set_child(self.browser_grid)
        scrolled.set_min_content_height(120)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(scrolled)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.append(header)
        outer_box.append(self.toast_overlay)

        self.set_content(outer_box)

        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
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
            self.show_banner()

        browsers = Gio.AppInfo.get_all_for_type(app.content_types[1])
        browsers = [b for b in browsers if app.get_application_id() not in b.get_id()]
        self.browsers = self.dedupe_browsers(browsers)

        url = self.entry.get_text()
        mapped = app.browser_mappings.determine_browser(url, browsers)
        if mapped is not None:
            mapped.launch_uris([url])
            self.close()
            return

        if not self.browsers:
            empty = Adw.StatusPage(
                title=_("No browsers found"),
                description=_(
                    "Install a browser, or check that its desktop file "
                    "registers the x-scheme-handler/https MIME type."
                ),
                icon_name="preferences-web-browser-symbolic",
            )
            self.toast_overlay.set_child(empty)
            return

        for index, browser in enumerate(self.browsers):
            self.browser_grid.append(self.create_browser_card(app, index, browser))

    @staticmethod
    def dedupe_browsers(browsers):
        seen = set()
        unique = []
        for browser in browsers:
            executable = browser.get_executable() or ""
            name = browser.get_display_name()
            key = (executable, name)
            if key in seen:
                continue
            seen.add(key)
            unique.append(browser)
        return unique

    def show_banner(self):
        self.banner = Adw.Banner(
            title=_("Set Braus as your default browser")
        )
        self.banner.set_button_label(_("Set as Default"))
        self.banner.set_action_name("win.set-default")
        self.get_content().prepend(self.banner)

    def remove_banner(self):
        if self.banner is not None:
            self.banner.unparent()
            self.banner = None

    def create_browser_card(self, app, index, browser):
        gicon = browser.get_icon()
        if gicon is not None:
            icon = Gtk.Image.new_from_gicon(gicon)
        else:
            icon = Gtk.Image.new_from_icon_name('applications-internet')
        icon.set_pixel_size(48)
        icon.set_valign(Gtk.Align.START)

        label = Gtk.Label.new(browser.get_display_name())
        label.set_max_width_chars(12)
        label.set_wrap(True)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_justify(Gtk.Justification.CENTER)

        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        button_box.set_margin_top(6)
        button_box.set_margin_bottom(6)
        button_box.set_margin_start(8)
        button_box.set_margin_end(8)
        button_box.append(icon)
        button_box.append(label)

        button = Gtk.Button()
        button.set_child(button_box)
        button.add_css_class("flat")
        button.set_tooltip_text(
            _("Open with {}").format(browser.get_display_name())
        )
        button.connect("clicked", self.on_browser_clicked, index, app)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.append(button)
        if index < 10:
            hotkey_name = str((index + 1) % 10)
            hotkey_label = Gtk.Label(label=hotkey_name)
            hotkey_label.add_css_class("dim-label")
            hotkey_label.set_valign(Gtk.Align.END)
            card.append(hotkey_label)

        card_widget = Gtk.FlowBoxChild()
        card_widget.set_child(card)
        return card_widget

    def on_entry_clicked(self, gesture, n_press, x, y):
        self.entry.set_can_focus(True)
        self.entry.grab_focus()

    def on_key_pressed(self, controller, keyval, keycode, state, app):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        if self.launching:
            return False
        entry_focus = self.get_focus_child() is self.entry
        entry_editing = self.entry.get_state_flags() & Gtk.StateFlags.FOCUS_WITHIN
        if entry_focus or entry_editing:
            return False
        if Gdk.KEY_KP_0 <= keyval <= Gdk.KEY_KP_9:
            digit = keyval - Gdk.KEY_KP_0
        elif Gdk.KEY_0 <= keyval <= Gdk.KEY_9:
            digit = keyval - Gdk.KEY_0
        else:
            return False
        index = (digit - 1) % 10
        if 0 <= index < len(self.browsers):
            self.launch_browser(index, app)
            return True
        return False

    def on_entry_activated(self, entry, app):
        if self.browsers:
            self.launch_browser(0, app)

    def on_browser_clicked(self, button, index, app):
        self.launch_browser(index, app)

    def launch_browser(self, index, app):
        if self.launching:
            return
        self.launching = True
        browser = self.browsers[index]
        browser.launch_uris([self.entry.get_text()])
        toast = Adw.Toast(
            title=_("Opening {}…").format(browser.get_display_name())
        )
        self.toast_overlay.add_toast(toast)
        GLib.timeout_add(500, self.close)

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
        self.remove_banner()
        toast = Adw.Toast(title=_("Braus is now your default browser"))
        self.toast_overlay.add_toast(toast)

    def on_never_ask(self, action, param, app):
        app.settings.set_boolean("ask-default", False)
        self.remove_banner()
        toast = Adw.Toast(title=_("Okay, we won't ask again"))
        self.toast_overlay.add_toast(toast)
