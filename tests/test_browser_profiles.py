import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

spec = importlib.util.spec_from_file_location(
    "browser_profiles",
    Path(__file__).resolve().parent.parent / "src" / "browser_profiles.py",
)
browser_profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser_profiles)


class DetectProfileKindTests(unittest.TestCase):
    def test_chrome_is_chromium(self):
        key = "google-chrome.desktop /usr/bin/google-chrome %u"
        self.assertEqual(
            browser_profiles.detect_profile_kind(key),
            browser_profiles.PROFILE_KIND_CHROMIUM,
        )

    def test_firefox_is_firefox(self):
        key = "firefox.desktop firefox %u"
        self.assertEqual(
            browser_profiles.detect_profile_kind(key),
            browser_profiles.PROFILE_KIND_FIREFOX,
        )

    def test_flatpak_firefox_is_firefox(self):
        key = "org.mozilla.firefox.desktop firefox %u flatpak"
        self.assertEqual(
            browser_profiles.detect_profile_kind(key),
            browser_profiles.PROFILE_KIND_FIREFOX,
        )

    def test_epiphany_is_unknown(self):
        key = "org.gnome.Epiphany.desktop epiphany %u"
        self.assertIsNone(browser_profiles.detect_profile_kind(key))

    def test_empty_key(self):
        self.assertIsNone(browser_profiles.detect_profile_kind(""))


class LaunchArgsTests(unittest.TestCase):
    def test_chromium_profile_and_incognito(self):
        args = browser_profiles.launch_args(
            "google-chrome.desktop", "Profile 1", True
        )
        self.assertEqual(
            args, ["--profile-directory=Profile 1", "--incognito"]
        )

    def test_firefox_profile_and_private(self):
        args = browser_profiles.launch_args("firefox.desktop", "work", True)
        self.assertEqual(args, ["-P", "work", "--private-window"])

    def test_chromium_incognito_only(self):
        args = browser_profiles.launch_args("chromium.desktop", None, True)
        self.assertEqual(args, ["--incognito"])

    def test_firefox_profile_only(self):
        args = browser_profiles.launch_args("librewolf.desktop", "default", False)
        self.assertEqual(args, ["-P", "default"])

    def test_unknown_browser_no_args(self):
        self.assertEqual(
            browser_profiles.launch_args("org.gnome.Epiphany.desktop", "x", True),
            [],
        )


class BuildCommandTests(unittest.TestCase):
    def test_field_codes_replaced(self):
        command = browser_profiles.build_command(
            "/usr/bin/google-chrome %u",
            "https://example.com",
            ["--incognito"],
        )
        self.assertEqual(
            command,
            ["/usr/bin/google-chrome", "--incognito", "https://example.com"],
        )

    def test_no_field_codes_appends(self):
        command = browser_profiles.build_command(
            "/usr/bin/firefox", "https://example.com", ["-P", "work"]
        )
        self.assertEqual(
            command,
            ["/usr/bin/firefox", "-P", "work", "https://example.com"],
        )

    def test_icon_codes_removed(self):
        command = browser_profiles.build_command(
            "app %i %u", "https://example.com", []
        )
        self.assertEqual(command, ["app", "https://example.com"])

    def test_escaped_percent(self):
        command = browser_profiles.build_command(
            "app %% %u", "https://example.com", []
        )
        self.assertEqual(command, ["app", "%", "https://example.com"])


class ListProfilesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        home = Path(self._tmp.name)
        self._env = {
            "HOME": os.environ.get("HOME"),
            "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME"),
        }
        os.environ["HOME"] = str(home)
        os.environ["XDG_CONFIG_HOME"] = str(home / ".config")

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def test_chromium_profiles_from_local_state(self):
        home = Path(self._tmp.name)
        state_dir = home / ".config" / "google-chrome"
        state_dir.mkdir(parents=True)
        info = {
            "Default": {"name": "Person 1"},
            "Profile 1": {"name": "Work"},
        }
        (state_dir / "Local State").write_text(
            json.dumps({"profile": {"info_cache": info}}), encoding="utf-8"
        )
        profiles = browser_profiles.list_profiles("google-chrome.desktop")
        self.assertEqual([p.name for p in profiles], ["Person 1", "Work"])

    def test_firefox_profiles_from_ini(self):
        home = Path(self._tmp.name)
        firefox_dir = home / ".mozilla" / "firefox"
        firefox_dir.mkdir(parents=True)
        ini = "\n".join(
            [
                "[Profile1]",
                "Name=work",
                "Path=xxxx.work",
                "IsRelative=1",
                "",
                "[Profile0]",
                "Name=default",
                "Path=xxxx.default",
                "Default=1",
                "IsRelative=1",
                "",
                "[General]",
                "StartWithLastProfile=1",
            ]
        )
        (firefox_dir / "profiles.ini").write_text(ini, encoding="utf-8")
        profiles = browser_profiles.list_profiles("firefox.desktop")
        self.assertEqual([p.name for p in profiles], ["default", "work"])

    def test_unknown_browser_no_profiles(self):
        self.assertEqual(browser_profiles.list_profiles("epiphany.desktop"), [])


if __name__ == "__main__":
    unittest.main()
