from gi.repository import Gio, GLib


class BrowserMappings:
    def __init__(self, settings: Gio.Settings):
        self.settings = settings

    def set_browser(self, url: str, browser: str) -> None:
        mappings = [m for m in self.load() if m[0] != url]
        mappings.append([url, browser])
        self.settings.set_value("url-mapping", GLib.Variant('a(ss)', mappings))

    def clear(self) -> None:
        self.settings.set_value("url-mapping", GLib.Variant('a(ss)', []))

    def load(self) -> list[list[str]]:
        return [list(mapping) for mapping in self.settings.get_value("url-mapping")]

    def determine_browser(self, url: str, browsers):
        for prefix, browser_id in self.load():
            if not url.startswith(prefix):
                continue
            for browser in browsers:
                if browser.get_id() == browser_id:
                    return browser
        return None
