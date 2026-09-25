from urllib.parse import urlparse

SCOPE_URL = "url"
SCOPE_PATH = "path"
SCOPE_DOMAIN = "domain"

SCOPES = (SCOPE_URL, SCOPE_PATH, SCOPE_DOMAIN)


def scoped_url(url: str, scope: str) -> str:
    if scope == SCOPE_URL:
        return url
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    userinfo, sep, host = parsed.netloc.rpartition("@")
    netloc = f"{userinfo}{sep}{host.lower()}" if sep else host.lower()
    if scope == SCOPE_DOMAIN:
        if parsed.hostname is None:
            return url
        return f"{parsed.scheme}://{parsed.hostname.lower()}"
    if scope == SCOPE_PATH:
        if not parsed.path:
            return f"{parsed.scheme}://{netloc}"
        return f"{parsed.scheme}://{netloc}{parsed.path}"
    return url


def infer_scope(url):
    """Guess which scope a stored prefix represents, for display purposes."""
    if not url:
        return SCOPE_URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return SCOPE_URL
    if parsed.path not in ("", "/"):
        return SCOPE_PATH
    return SCOPE_DOMAIN
