import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

spec = importlib.util.spec_from_file_location(
    "url_scopes", Path(__file__).resolve().parent.parent / "src" / "url_scopes.py"
)
url_scopes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(url_scopes)


class ScopedUrlTests(unittest.TestCase):
    def test_scope_url_is_unchanged(self):
        self.assertEqual(
            url_scopes.scoped_url("https://example.com/a?b=1#c", url_scopes.SCOPE_URL),
            "https://example.com/a?b=1#c",
        )

    def test_scope_path_strips_query_and_fragment(self):
        self.assertEqual(
            url_scopes.scoped_url(
                "https://example.com/docs/page.html?x=1#top", url_scopes.SCOPE_PATH
            ),
            "https://example.com/docs/page.html",
        )

    def test_scope_path_root(self):
        self.assertEqual(
            url_scopes.scoped_url("https://example.com", url_scopes.SCOPE_PATH),
            "https://example.com",
        )

    def test_scope_path_empty_path(self):
        self.assertEqual(
            url_scopes.scoped_url("https://example.com?q=1", url_scopes.SCOPE_PATH),
            "https://example.com",
        )

    def test_scope_domain(self):
        self.assertEqual(
            url_scopes.scoped_url(
                "https://user:pw@Example.COM:8443/a/b?c=1", url_scopes.SCOPE_DOMAIN
            ),
            "https://example.com",
        )

    def test_domain_is_lowercased(self):
        self.assertEqual(
            url_scopes.scoped_url("https://EXAMPLE.com/Page", url_scopes.SCOPE_DOMAIN),
            "https://example.com",
        )

    def test_port_is_kept_for_path(self):
        self.assertEqual(
            url_scopes.scoped_url("https://example.com:8080/x", url_scopes.SCOPE_PATH),
            "https://example.com:8080/x",
        )

    def test_invalid_url_is_unchanged(self):
        self.assertEqual(
            url_scopes.scoped_url("not a url", url_scopes.SCOPE_DOMAIN),
            "not a url",
        )


class InferScopeTests(unittest.TestCase):
    def test_url_with_path_is_path_scope(self):
        self.assertEqual(
            url_scopes.infer_scope("https://example.com/docs/page"),
            url_scopes.SCOPE_PATH,
        )

    def test_bare_domain_is_domain_scope(self):
        self.assertEqual(
            url_scopes.infer_scope("https://example.com"),
            url_scopes.SCOPE_DOMAIN,
        )

    def test_root_path_is_domain_scope(self):
        self.assertEqual(
            url_scopes.infer_scope("https://example.com/"),
            url_scopes.SCOPE_DOMAIN,
        )

    def test_non_url_is_url_scope(self):
        self.assertEqual(
            url_scopes.infer_scope("my-fancy-prefix"),
            url_scopes.SCOPE_URL,
        )

    def test_empty_is_url_scope(self):
        self.assertEqual(url_scopes.infer_scope(""), url_scopes.SCOPE_URL)


if __name__ == "__main__":
    unittest.main()
