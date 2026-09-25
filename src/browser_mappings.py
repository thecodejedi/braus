from gi.repository import Gio, GLib


class BrowserMappings:
    def __init__(self, settings: Gio.Settings):
        self.settings = settings

    def set_browser(self, url: str, browser: str) -> None:
        mappings = dict(self.load())
        mappings[url] = browser
        self.settings.set_value(
            "url-mapping", GLib.Variant('a(ss)', [[k, v] for k, v in mappings.items()])
        )

    def set_options(self, prefix: str, profile=None, incognito=False) -> None:
        options = {
            rule[0]: rule
            for rule in self.load_options()
        }
        options[prefix] = [prefix, profile or "", incognito, []]
        self.settings.set_value(
            "rule-options",
            GLib.Variant('a(sssa(ss))', list(options.values())),
        )

    def clear(self) -> None:
        self.settings.set_value("url-mapping", GLib.Variant('a(ss)', []))
        self.settings.set_value("rule-options", GLib.Variant('a(sssa(ss))', []))

    def load(self) -> list[list[str]]:
        return [list(mapping) for mapping in self.settings.get_value("url-mapping")]

    def load_options(self) -> list[list]:
        return [list(rule) for rule in self.settings.get_value("rule-options")]

    def determine_browser(self, url: str, browsers):
        url = url.lower()
        for prefix, browser_id in self.load():
            if not url.startswith(prefix.lower()):
                continue
            for browser in browsers:
                if browser.get_id() == browser_id:
                    return browser
        return None

    def determine_options(self, url: str):
        url = url.lower()
        for prefix, profile, incognito, _extra in self.load_options():
            if not url.startswith(prefix.lower()):
                continue
            return profile or None, bool(incognito)
        return None, False
