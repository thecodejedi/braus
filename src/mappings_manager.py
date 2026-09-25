# mappings_manager.py
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

from gi.repository import Adw, Gio, Gtk  # noqa: E402

from braus.browser_profiles import (  # noqa: E402
    list_profiles,
    profile_identifier,
)


def _profile_key(browser):
    parts = [
        browser.get_id() or "",
        browser.get_display_name() or "",
        browser.get_executable() or "",
        browser.get_commandline() or "",
    ]
    return " ".join(parts)


class MappingsManagerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'BrausMappingsManagerWindow'

    def __init__(self, app):
        super().__init__(
            title=_("URL Rules"),
            application=app,
            default_width=480,
            default_height=450,
        )
        self.browsers = self.load_browsers(app)

        header = Adw.HeaderBar()

        add_action = Gio.SimpleAction.new("add", None)
        add_action.connect("activate", self.on_add)
        self.add_action(add_action)

        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.set_action_name("win.add")
        add_button.set_tooltip_text(_("Add rule"))
        header.pack_start(add_button)

        self.status_page = Adw.StatusPage(
            title=_("No URL rules"),
            description=_(
                "URL rules open matching links in a fixed browser "
                "without showing the picker. Add one with the + button."
            ),
            icon_name="preferences-web-browser-symbolic",
        )

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.status_page)

        self.content = Adw.ToolbarView()
        self.content.add_top_bar(header)
        self.content.set_content(self.toast_overlay)
        self.set_content(self.content)

        self.populate()

    @staticmethod
    def load_browsers(app):
        browsers = Gio.AppInfo.get_all_for_type(app.content_types[1])
        return {
            browser.get_id(): browser
            for browser in browsers
            if app.get_application_id() not in browser.get_id()
        }

    def populate(self):
        rules = self.app.browser_mappings.load_rules()
        if not rules:
            self.toast_overlay.set_child(self.status_page)
            return
        group = Adw.PreferencesGroup(title=_("URL Rules"))
        for rule in rules:
            group.add(self.create_rule_row(rule))
        scrolled = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
        )
        scrolled.set_child(group)
        scrolled.set_margin_top(12)
        scrolled.set_margin_bottom(12)
        self.toast_overlay.set_child(scrolled)

    def create_rule_row(self, rule):
        row = Adw.ActionRow(title=rule.prefix)
        row.set_title_lines(1)
        browser = self.browsers.get(rule.browser_id)
        if browser is not None:
            subtitle = browser.get_display_name()
            gicon = browser.get_icon()
            if gicon is not None:
                icon = Gtk.Image.new_from_gicon(gicon)
                icon.set_pixel_size(24)
                icon.set_valign(Gtk.Align.CENTER)
                row.add_prefix(icon)
        else:
            subtitle = rule.browser_id
            warning = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            warning.set_valign(Gtk.Align.CENTER)
            warning.set_tooltip_text(
                _("No installed browser matches \"{}\"").format(rule.browser_id)
            )
            row.add_suffix(warning)
            row.add_css_class("warning")
        if rule.profile:
            subtitle = f"{subtitle} — {rule.profile}"
        if rule.incognito:
            subtitle = f"{subtitle} ({_('private')})"
        row.set_subtitle(subtitle)
        edit_button = Gtk.Button()
        edit_button.set_icon_name("document-edit-symbolic")
        edit_button.set_valign(Gtk.Align.CENTER)
        edit_button.set_tooltip_text(_("Edit rule"))
        edit_button.add_css_class("flat")
        edit_button.connect("clicked", self.on_edit, rule)
        row.add_suffix(edit_button)
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.set_valign(Gtk.Align.CENTER)
        delete_button.set_tooltip_text(_("Delete rule"))
        delete_button.add_css_class("flat")
        delete_button.connect("clicked", self.on_delete, rule.prefix)
        row.add_suffix(delete_button)
        return row

    def on_add(self, action, param):
        RuleEditorDialog(self, None).present()

    def on_edit(self, button, rule):
        RuleEditorDialog(self, rule).present()

    def on_delete(self, button, prefix):
        self.app.browser_mappings.remove_rule(prefix)
        self.populate()
        self.toast(_("Removed rule for \"{}\"").format(prefix))

    def toast(self, title):
        self.toast_overlay.add_toast(Adw.Toast(title=title, timeout=2))

    @property
    def app(self):
        return self.get_application()


class RuleEditorDialog(Adw.AlertDialog):
    __gtype_name__ = 'BrausRuleEditorDialog'

    def __init__(self, manager, existing):
        is_edit = existing is not None
        super().__init__(
            heading=_("Edit rule") if is_edit else _("Add rule"),
            body=_("Opens URLs starting with the prefix without showing the picker."),
        )
        self.manager = manager
        self.existing = existing
        self.check_buttons = {}

        self.url_entry = Adw.EntryRow(title=_("URL prefix"))
        if is_edit:
            self.url_entry.set_text(existing.prefix)

        browser_group = Adw.PreferencesGroup(title=_("Browser"))
        for browser in sorted(
            manager.browsers.values(),
            key=lambda browser: browser.get_display_name().lower(),
        ):
            check = Gtk.CheckButton()
            check.connect("toggled", self.on_browser_toggled)
            self.check_buttons[browser.get_id()] = check
            row = Adw.ActionRow(title=browser.get_display_name())
            gicon = browser.get_icon()
            if gicon is not None:
                icon = Gtk.Image.new_from_gicon(gicon)
                icon.set_pixel_size(24)
                icon.set_valign(Gtk.Align.CENTER)
                row.add_prefix(icon)
            row.add_prefix(check)
            row.set_activatable_widget(check)
            browser_group.add(row)

        self.profile_row = Adw.ComboRow(title=_("Profile"))
        profile_model = Gtk.StringList()
        profile_model.append(_("Default profile"))
        self.profile_row.set_model(profile_model)
        browser_group.add(self.profile_row)

        self.private_switch = Gtk.Switch()
        self.private_switch.set_valign(Gtk.Align.CENTER)
        private_row = Adw.ActionRow(title=_("Open in private window"))
        private_row.add_suffix(self.private_switch)
        private_row.set_activatable_widget(self.private_switch)
        browser_group.add(private_row)

        scrolled = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
        )
        scrolled.set_child(browser_group)
        scrolled.set_min_content_height(180)
        scrolled.set_margin_top(6)
        scrolled.set_margin_bottom(6)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        url_group = Adw.PreferencesGroup()
        url_group.add(self.url_entry)
        box.append(url_group)
        box.append(scrolled)

        self.set_extra_child(box)
        self.add_response("cancel", _("Cancel"))
        self.add_response("save", _("Save"))
        self.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        self.set_default_response("save")
        self.set_close_response("cancel")
        self.connect("response", self.on_response)

        if is_edit:
            self.select_browser(existing.browser_id, existing.profile)
            self.private_switch.set_active(existing.incognito)
        else:
            first = next(iter(self.check_buttons))
            if first is not None:
                self.check_buttons[first].set_active(True)

    def on_browser_toggled(self, check):
        if not check.get_active():
            return
        self.refresh_profiles(self._active_browser_id())

    def _active_browser_id(self):
        for browser_id, button in self.check_buttons.items():
            if button.get_active():
                return browser_id
        return None

    def browser_profiles(self, browser_id):
        browser = self.manager.browsers.get(browser_id)
        if browser is None:
            return []
        return list_profiles(_profile_key(browser))

    def refresh_profiles(self, browser_id):
        self.profile_row.get_model().splice(
            0, self.profile_row.get_model().get_n_items(), []
        )
        for profile in self.browser_profiles(browser_id):
            self.profile_row.get_model().append(profile.name)

    def select_browser(self, browser_id, profile):
        check = self.check_buttons.get(browser_id)
        if check is None:
            if self.check_buttons:
                self.check_buttons[next(iter(self.check_buttons))].set_active(True)
            return
        check.set_active(True)
        self.refresh_profiles(browser_id)
        model = self.profile_row.get_model()
        for candidate in self.browser_profiles(browser_id):
            if candidate.name == profile or candidate.directory == profile:
                for index in range(model.get_n_items()):
                    if model.get_string(index) == candidate.name:
                        self.profile_row.set_selected(index)
                        return
        self.profile_row.set_selected(0)

    def selected_profile_id(self):
        model = self.profile_row.get_model()
        index = self.profile_row.get_selected()
        if index == 0 or index == Gtk.INVALID_LIST_POSITION:
            return None
        name = model.get_string(index)
        browser_id = self._active_browser_id()
        browser = self.manager.browsers.get(browser_id)
        if browser is None:
            return None
        for candidate in list_profiles(_profile_key(browser)):
            if candidate.name == name:
                return profile_identifier(_profile_key(browser), candidate)
        return None

    def on_response(self, dialog, response):
        if response != "save":
            self.close()
            return
        prefix = self.url_entry.get_text().strip()
        if not prefix:
            self.manager.toast(_("Enter a URL prefix"))
            return
        browser_id = self._active_browser_id()
        if browser_id is None:
            self.manager.toast(_("Pick a browser"))
            return
        mappings = self.manager.app.browser_mappings
        if self.existing is not None and self.existing.prefix.lower() != prefix.lower():
            mappings.remove_rule(self.existing.prefix)
        mappings.set_browser(prefix, browser_id)
        mappings.set_options(
            prefix, self.selected_profile_id(), self.private_switch.get_active()
        )
        self.manager.populate()
        if self.existing is None:
            self.manager.toast(_("Added rule for \"{}\"").format(prefix))
        else:
            self.manager.toast(_("Updated rule for \"{}\"").format(prefix))
        self.close()
