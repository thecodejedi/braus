import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

spec = importlib.util.spec_from_file_location(
    "rule_args",
    Path(__file__).resolve().parent.parent / "src" / "rule_args.py",
)
rule_args = importlib.util.module_from_spec(spec)
sys.modules["rule_args"] = rule_args
try:
    spec.loader.exec_module(rule_args)
except ModuleNotFoundError:
    rule_args = None


@unittest.skipIf(rule_args is None, "rule_args module unavailable")
class ParseSetArgsTests(unittest.TestCase):
    def test_plain_prefix_and_browser(self):
        spec = rule_args.parse_set_args(
            ["https://example.com", "firefox.desktop"]
        )
        self.assertEqual(spec.url, "https://example.com")
        self.assertEqual(spec.browser_id, "firefox.desktop")
        self.assertEqual(spec.scope, "url")
        self.assertEqual(spec.profile, "")
        self.assertFalse(spec.private)

    def test_scope_long_option(self):
        spec = rule_args.parse_set_args(
            ["https://example.com/docs", "a.desktop", "--scope", "path"]
        )
        self.assertEqual(spec.scope, "path")

    def test_scope_equals_form(self):
        spec = rule_args.parse_set_args(
            ["https://EXAMPLE.com/x", "a.desktop", "--scope=domain"]
        )
        self.assertEqual(spec.scope, "domain")

    def test_profile_long_option(self):
        spec = rule_args.parse_set_args(
            ["https://example.com", "a.desktop", "--profile", "work"]
        )
        self.assertEqual(spec.profile, "work")

    def test_profile_equals_form(self):
        spec = rule_args.parse_set_args(
            ["https://example.com", "a.desktop", "--profile=work"]
        )
        self.assertEqual(spec.profile, "work")

    def test_private_flag(self):
        spec = rule_args.parse_set_args(
            ["https://example.com", "a.desktop", "--private"]
        )
        self.assertTrue(spec.private)

    def test_all_options_combined(self):
        spec = rule_args.parse_set_args(
            [
                "https://example.com/docs/page",
                "a.desktop",
                "--scope", "path",
                "--profile", "work",
                "--private",
            ]
        )
        self.assertEqual(spec.scope, "path")
        self.assertEqual(spec.profile, "work")
        self.assertTrue(spec.private)

    def test_options_before_positional(self):
        spec = rule_args.parse_set_args(
            ["--private", "--scope", "domain", "https://example.com", "a.desktop"]
        )
        self.assertEqual(spec.scope, "domain")
        self.assertTrue(spec.private)
        self.assertEqual(spec.url, "https://example.com")

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args(
                ["https://example.com", "a.desktop", "--scope", "nope"]
            )

    def test_unknown_option_rejected(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args(
                ["https://example.com", "a.desktop", "--wat"]
            )

    def test_missing_positional_args(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args(["https://example.com"])

    def test_no_args(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args([])

    def test_missing_scope_value(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args(
                ["https://example.com", "a.desktop", "--scope"]
            )

    def test_missing_profile_value(self):
        with self.assertRaises(ValueError):
            rule_args.parse_set_args(
                ["https://example.com", "a.desktop", "--profile"]
            )


if __name__ == "__main__":
    unittest.main()
