import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class FakeSettings:
    def __init__(self):
        self.values = {}

    def get_value(self, key):
        return self.values.get(key, [])

    def set_value(self, key, value):
        self.values[key] = value


spec = importlib.util.spec_from_file_location(
    "browser_mappings",
    Path(__file__).resolve().parent.parent / "src" / "browser_mappings.py",
)
browser_mappings = importlib.util.module_from_spec(spec)


class FakeVariant:
    def __init__(self, type_string, value):
        self.type_string = type_string
        self.value = value

    def __iter__(self):
        return iter(self.value)


def _fake_glib_variant(type_string, value):
    return FakeVariant(type_string, value)


class _FakeGLib:
    @staticmethod
    def Variant(type_string, value):
        return _fake_glib_variant(type_string, value)


class _FakeGio:
    class Settings:  # noqa: N801
        pass


sys.modules["gi"] = type(sys)("gi")
sys.modules["gi.repository"] = type(sys)("gi.repository")
sys.modules["gi.repository"].Gio = _FakeGio
sys.modules["gi.repository"].GLib = _FakeGLib
try:
    spec.loader.exec_module(browser_mappings)
finally:
    pass


class BrowserMappingsTests(unittest.TestCase):
    def setUp(self):
        self.settings = FakeSettings()
        self.mappings = browser_mappings.BrowserMappings(self.settings)

    def test_set_browser_stores_mapping(self):
        self.mappings.set_browser("https://example.com", "firefox.desktop")
        self.assertEqual(
            self.mappings.load(),
            [["https://example.com", "firefox.desktop"]],
        )

    def test_set_browser_overwrites_same_prefix(self):
        self.mappings.set_browser("https://example.com", "firefox.desktop")
        self.mappings.set_browser("https://example.com", "chrome.desktop")
        self.assertEqual(len(self.mappings.load()), 1)
        self.assertEqual(
            self.mappings.load(),
            [["https://example.com", "chrome.desktop"]],
        )

    def test_set_options_stores_profile_and_private(self):
        self.mappings.set_options("https://example.com", "work", True)
        options = self.mappings.load_options()
        self.assertEqual(len(options), 1)
        prefix, profile, incognito, extra = options[0]
        self.assertEqual(prefix, "https://example.com")
        self.assertEqual(profile, "work")
        self.assertEqual(incognito, "1")
        self.assertEqual(extra, [])

    def test_set_options_overwrites_same_prefix(self):
        self.mappings.set_options("https://example.com", "work", True)
        self.mappings.set_options("https://example.com", None, False)
        options = self.mappings.load_options()
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0][1], "")
        self.assertEqual(options[0][2], "")

    def test_determine_options_matches_prefix_case_insensitive(self):
        self.mappings.set_options("https://EXAMPLE.com", "work", True)
        profile, incognito = self.mappings.determine_options(
            "https://example.com/page"
        )
        self.assertEqual(profile, "work")
        self.assertTrue(incognito)

    def test_determine_options_no_match(self):
        self.mappings.set_options("https://example.com", "work", True)
        profile, incognito = self.mappings.determine_options(
            "https://other.org"
        )
        self.assertIsNone(profile)
        self.assertFalse(incognito)

    def test_determine_options_empty_profile_returns_none(self):
        self.mappings.set_options("https://example.com", None, False)
        profile, incognito = self.mappings.determine_options(
            "https://example.com/x"
        )
        self.assertIsNone(profile)
        self.assertFalse(incognito)

    def test_clear_removes_options_and_mappings(self):
        self.mappings.set_browser("https://example.com", "firefox.desktop")
        self.mappings.set_options("https://example.com", "work", True)
        self.mappings.clear()
        self.assertEqual(self.mappings.load(), [])
        self.assertEqual(self.mappings.load_options(), [])


if __name__ == "__main__":
    unittest.main()
