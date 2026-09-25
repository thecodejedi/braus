from dataclasses import dataclass
from gettext import gettext as _

try:
    from braus.url_scopes import SCOPES, SCOPE_URL  # noqa: E402
except ImportError:
    from url_scopes import SCOPES, SCOPE_URL  # noqa: E402


@dataclass(frozen=True)
class RuleSpec:
    url: str
    browser_id: str
    scope: str = SCOPE_URL
    profile: str = ""
    private: bool = False


def parse_set_args(args):
    """Parse the arguments of ``braus --set``.

    Accepts ``<url> <browser.desktop>`` followed by any combination of
    ``--scope url|path|domain``, ``--profile NAME`` and ``--private``.
    Raises ValueError with a user-facing message on invalid input.
    """
    positional = []
    scope = SCOPE_URL
    profile = ""
    private = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--scope":
            i += 1
            if i >= len(args):
                raise ValueError(_("Missing value for --scope"))
            scope = args[i]
        elif arg.startswith("--scope="):
            scope = arg.split("=", 1)[1]
        elif arg == "--profile":
            i += 1
            if i >= len(args):
                raise ValueError(_("Missing value for --profile"))
            profile = args[i]
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
        elif arg == "--private":
            private = True
        elif arg.startswith("--"):
            raise ValueError(_("Unknown option: {}").format(arg))
        else:
            positional.append(arg)
        i += 1

    if scope not in SCOPES:
        raise ValueError(
            _("Invalid scope \"{}\". Use one of: {}").format(
                scope, ", ".join(SCOPES)
            )
        )
    if len(positional) < 2:
        raise ValueError(
            _("Usage: braus --set <url> <browser.desktop> "
              "[--scope url|path|domain] [--profile NAME] [--private]")
        )
    url = positional[0]
    browser_id = positional[1]
    if not url:
        raise ValueError(_("Missing URL"))
    if not browser_id:
        raise ValueError(_("Missing browser"))
    return RuleSpec(
        url=url, browser_id=browser_id, scope=scope,
        profile=profile, private=private,
    )
