from gi.repository import Gio, GLib

try:
    from braus.url_rules import combined_rules, match_rule  # noqa: E402
except ImportError:
    from url_rules import combined_rules, match_rule  # noqa: E402


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
        options[prefix] = [prefix, profile or "", "1" if incognito else "", []]
        self.settings.set_value(
            "rule-options",
            GLib.Variant('a(sssa(ss))', list(options.values())),
        )

    def set_rule(
        self, prefix: str, browser_id: str, profile=None, incognito=False
    ) -> None:
        self.set_browser(prefix, browser_id)
        self.set_options(prefix, profile, incognito)

    def remove_rule(self, prefix: str) -> None:
        mappings = {
            url: browser
            for url, browser in ((entry[0], entry[1]) for entry in self.load())
            if url.lower() != prefix.lower()
        }
        self.settings.set_value(
            "url-mapping", GLib.Variant('a(ss)', list(mappings.items()))
        )
        options = [
            rule for rule in self.load_options()
            if str(rule[0]).lower() != prefix.lower()
        ]
        self.settings.set_value(
            "rule-options", GLib.Variant('a(sssa(ss))', options),
        )

    def clear(self) -> None:
        self.settings.set_value("url-mapping", GLib.Variant('a(ss)', []))
        self.settings.set_value("rule-options", GLib.Variant('a(sssa(ss))', []))

    def load(self) -> list[list[str]]:
        return [list(mapping) for mapping in self.settings.get_value("url-mapping")]

    def load_options(self) -> list[list]:
        return [list(rule) for rule in self.settings.get_value("rule-options")]

    def determine_browser(self, url: str, browsers):
        rule = match_rule(self.load_rules(), url)
        if rule is None:
            return None
        for browser in browsers:
            if browser.get_id() == rule.browser_id:
                return browser
        return None

    def determine_options(self, url: str):
        url = (url or "").lower()
        best = None
        for prefix, profile, incognito, _extra in self.load_options():
            prefix_lower = str(prefix).lower()
            if not prefix_lower or not url.startswith(prefix_lower):
                continue
            if best is None or len(prefix_lower) > len(best[0]):
                best = (prefix_lower, profile, incognito)
        if best is None:
            return None, False
        return best[1] or None, str(best[2]) == "1"

    def load_rules(self):
        return combined_rules(self.load(), self.load_options())
