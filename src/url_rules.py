from dataclasses import dataclass

try:
    from braus.url_scopes import infer_scope  # noqa: E402
except ImportError:
    from url_scopes import infer_scope  # noqa: E402


@dataclass(frozen=True)
class UrlRule:
    prefix: str
    browser_id: str
    profile: str = ""
    incognito: bool = False
    scope: str = ""


def combined_rules(mappings, options):
    options_by_prefix = {}
    for entry in options:
        prefix = str(entry[0])
        profile = str(entry[1]) if len(entry) > 1 and entry[1] else ""
        incognito = str(entry[2]) == "1" if len(entry) > 2 else False
        options_by_prefix[prefix] = (profile, incognito)
    rules = []
    for entry in mappings:
        prefix = str(entry[0])
        browser_id = str(entry[1])
        profile, incognito = options_by_prefix.get(prefix, ("", False))
        rules.append(
            UrlRule(
                prefix,
                browser_id,
                profile,
                incognito,
                infer_scope(prefix),
            )
        )
    return rules


def match_rule(rules, url):
    url = (url or "").lower()
    best = None
    for rule in rules:
        prefix = rule.prefix.lower()
        if prefix and url.startswith(prefix) and (
            best is None or len(prefix) > len(best.prefix)
        ):
            best = rule
    return best
