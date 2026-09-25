import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

spec = importlib.util.spec_from_file_location(
    "url_rules", Path(__file__).resolve().parent.parent / "src" / "url_rules.py"
)
url_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(url_rules)


class CombinedRulesTests(unittest.TestCase):
    def test_plain_mapping_without_options(self):
        rules = url_rules.combined_rules(
            [["https://example.com", "firefox.desktop"]], []
        )
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertEqual(rule.browser_id, "firefox.desktop")
        self.assertEqual(rule.profile, "")
        self.assertFalse(rule.incognito)

    def test_mapping_with_options(self):
        rules = url_rules.combined_rules(
            [["https://example.com", "firefox.desktop"]],
            [["https://example.com", "work", "1", []]],
        )
        rule = rules[0]
        self.assertEqual(rule.profile, "work")
        self.assertTrue(rule.incognito)

    def test_options_without_profile(self):
        rules = url_rules.combined_rules(
            [["https://example.com", "a.desktop"]],
            [["https://example.com", "", "1", []]],
        )
        self.assertEqual(rules[0].profile, "")
        self.assertTrue(rules[0].incognito)

    def test_options_for_other_prefix_ignored(self):
        rules = url_rules.combined_rules(
            [["https://a.example", "a.desktop"]],
            [["https://b.example", "work", False, []]],
        )
        self.assertEqual(rules[0].profile, "")

    def test_no_rules(self):
        self.assertEqual(url_rules.combined_rules([], []), [])

    def test_rule_scope_is_inferred(self):
        rules = url_rules.combined_rules(
            [
                ["https://example.com", "a.desktop"],
                ["https://example.com/docs", "b.desktop"],
                ["my-prefix", "c.desktop"],
            ],
            [],
        )
        self.assertEqual(rules[0].scope, "domain")
        self.assertEqual(rules[1].scope, "path")
        self.assertEqual(rules[2].scope, "url")


class MatchRuleTests(unittest.TestCase):
    def setUp(self):
        self.rules = url_rules.combined_rules(
            [
                ["https://example.com", "a.desktop"],
                ["https://example.com/docs", "b.desktop"],
            ],
            [],
        )

    def test_longest_prefix_wins(self):
        rule = url_rules.match_rule(self.rules, "https://example.com/docs/x")
        self.assertEqual(rule.browser_id, "b.desktop")

    def test_shorter_prefix_still_matches(self):
        rule = url_rules.match_rule(self.rules, "https://example.com/other")
        self.assertEqual(rule.browser_id, "a.desktop")

    def test_case_insensitive(self):
        rule = url_rules.match_rule(self.rules, "HTTPS://EXAMPLE.COM/DOCS")
        self.assertIsNotNone(rule)

    def test_no_match(self):
        self.assertIsNone(url_rules.match_rule(self.rules, "https://other.org"))

    def test_empty_url(self):
        self.assertIsNone(url_rules.match_rule(self.rules, ""))


class MatchRuleOptionsTests(unittest.TestCase):
    def setUp(self):
        self.rules = url_rules.combined_rules(
            [
                ["https://example.com", "a.desktop"],
                ["https://example.com/docs", "b.desktop"],
            ],
            [
                ["https://example.com", "personal", "", []],
                ["https://example.com/docs", "work", "1", []],
            ],
        )

    def test_longest_prefix_options_win(self):
        rule = url_rules.match_rule(self.rules, "https://example.com/docs/x")
        self.assertEqual(rule.browser_id, "b.desktop")
        self.assertEqual(rule.profile, "work")
        self.assertTrue(rule.incognito)

    def test_shorter_prefix_options_used_for_rest(self):
        rule = url_rules.match_rule(self.rules, "https://example.com/other")
        self.assertEqual(rule.profile, "personal")
        self.assertFalse(rule.incognito)


if __name__ == "__main__":
    unittest.main()
