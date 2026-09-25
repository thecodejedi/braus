import configparser
import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

PROFILE_KIND_CHROMIUM = "chromium"
PROFILE_KIND_FIREFOX = "firefox"

CHROMIUM_STATE_DIRS = {
    "ungoogled": ("ungoogled-chromium",),
    "thorium": ("Thorium",),
    "brave": ("BraveSoftware/Brave-Browser", "BraveSoftware/Brave-Browser-Stable"),
    "edge": ("microsoft-edge",),
    "vivaldi": ("vivaldi",),
    "opera": ("opera",),
    "chromium": ("chromium",),
    "chrome": ("google-chrome", "chrome"),
}

FIREFOX_STATE_DIRS = {
    "librewolf": (".librewolf",),
    "waterfox": (".waterfox",),
    "floorp": (".floorp",),
    "zen": (".zen",),
    "firefox": (".mozilla/firefox",),
}

FLATPAK_APP_ID = re.compile(
    r"\b(?:org|com|io|net|dev|app|page|pro|me|xyz)\.[A-Za-z0-9][A-Za-z0-9_.-]*\b"
)

SNAP_PATH = re.compile(r"/snap/([A-Za-z0-9][A-Za-z0-9_.-]*)/")


@dataclass(frozen=True)
class BrowserProfile:
    name: str
    directory: str


def detect_profile_kind(key):
    key = (key or "").lower()
    for token in FIREFOX_STATE_DIRS:
        if token in key:
            return PROFILE_KIND_FIREFOX
    for token in CHROMIUM_STATE_DIRS:
        if token in key:
            return PROFILE_KIND_CHROMIUM
    return None


def list_profiles(key):
    kind = detect_profile_kind(key)
    if kind is None:
        return []
    for state_dir in _state_dirs(kind, key):
        if kind == PROFILE_KIND_FIREFOX:
            profiles = _firefox_profiles(state_dir)
        else:
            profiles = _chromium_profiles(state_dir)
        if profiles:
            return profiles
    return []


def launch_args(key, profile=None, incognito=False):
    kind = detect_profile_kind(key)
    if kind is None:
        return []
    args = []
    if profile is not None:
        if kind == PROFILE_KIND_CHROMIUM:
            args.append(f"--profile-directory={profile}")
        else:
            args.extend(["-P", profile])
    if incognito:
        if kind == PROFILE_KIND_CHROMIUM:
            args.append("--incognito")
        else:
            args.append("--private-window")
    return args


def build_command(commandline, url, extra_args=()):
    if not commandline:
        return []
    command = []
    url_appended = False
    for arg in shlex.split(commandline):
        if arg in ("%u", "%U", "%f", "%F"):
            command.extend(extra_args)
            command.append(url)
            url_appended = True
        elif arg in ("%i", "%c", "%k"):
            continue
        elif arg == "%%":
            command.append("%")
        else:
            command.append(arg)
    if not url_appended and url:
        command.extend(extra_args)
        command.append(url)
    return command


def _config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _flatpak_bases(key):
    match = FLATPAK_APP_ID.search(key)
    if match is None:
        return []
    app_root = Path.home() / ".var" / "app" / match.group(1)
    return [app_root / "config", app_root]


def _snap_base(key):
    match = SNAP_PATH.search(key)
    if match is None:
        return None
    return Path.home() / "snap" / match.group(1) / "common"


def _state_dirs(kind, key):
    key = (key or "").lower()
    table = FIREFOX_STATE_DIRS if kind == PROFILE_KIND_FIREFOX else CHROMIUM_STATE_DIRS
    names = None
    for token, candidates in table.items():
        if token in key:
            names = candidates
            break
    if names is None:
        return
    bases = [Path.home() if kind == PROFILE_KIND_FIREFOX else _config_home()]
    snap_base = _snap_base(key)
    if snap_base is not None:
        bases.insert(0, snap_base)
    bases[:0] = _flatpak_bases(key)
    for base in bases:
        for name in names:
            yield base / name


def _firefox_profiles(state_dir):
    ini_file = state_dir / "profiles.ini"
    if not ini_file.is_file():
        return []
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(ini_file)
    except (configparser.Error, OSError):
        return []
    profiles = []
    for section in parser.sections():
        if not section.lower().startswith("profile"):
            continue
        name = parser.get(section, "Name", fallback=None)
        directory = parser.get(section, "Path", fallback=None)
        if not name or not directory:
            continue
        profile = BrowserProfile(name=name, directory=directory)
        default = parser.get(section, "Default", fallback="").lower() in ("1", "true")
        if default:
            profiles.insert(0, profile)
        else:
            profiles.append(profile)
    return profiles


def _chromium_profiles(state_dir):
    state_file = state_dir / "Local State"
    if not state_file.is_file():
        return []
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    info = data.get("profile", {}).get("info_cache", {})
    if not isinstance(info, dict):
        return []
    profiles = []
    for directory, entry in sorted(info.items()):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name") or directory
        profile = BrowserProfile(name=name, directory=directory)
        if directory == "Default":
            profiles.insert(0, profile)
        else:
            profiles.append(profile)
    return profiles
