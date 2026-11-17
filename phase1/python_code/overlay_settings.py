"""Runtime settings: env var, else a ``KEY=value`` file in an optional local overlay dir.

Overlay dir: ``LEARNING_HANDS_ON_LLM_OVERLAY_DIR`` set -> that dir (set to empty -> disabled);
unset -> the same key read from the dotfiles layer file
``${DOTFILES_DIR:-<main checkout>/../dotfiles}/shared-settings/`` (parsed, never sourced);
no key or no layer file -> no overlay.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

OVERLAY_DIR_ENV = "LEARNING_HANDS_ON_LLM_OVERLAY_DIR"
DOTFILES_DIR_ENV = "DOTFILES_DIR"
SETTINGS_FILE = "settings.env"  # overlay file name, and the dotfiles layer's file name
DOTFILES_LAYER = Path("shared-settings") / SETTINGS_FILE
# Shared contract with my-vector's bash reader: every non-blank, non-`#` line must match.
_LINE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=[^\s\"'$`#\\]*", re.ASCII)  # = bash LC_ALL=C [:space:]


def _main_root() -> Path:
    here = Path(__file__).resolve().parent
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=here,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return here.parents[1]
    return Path(common).parent


def _lines(path: Path) -> list[str]:
    # Bytes, not read_text: universal newlines would also split on a lone CR, which
    # the bash reader does not. utf-8-sig tolerates a leading BOM; CRLF is tolerated.
    return [raw.removesuffix("\r") for raw in path.read_bytes().decode("utf-8-sig").split("\n")]


def _dotfiles_pointer() -> Path | None:
    """The overlay dir named in the dotfiles layer; None when the layer file or the key is absent."""
    dotfiles = os.environ.get(DOTFILES_DIR_ENV) or _main_root().parent / "dotfiles"
    layer = Path(dotfiles) / DOTFILES_LAYER
    if not layer.is_file():
        return None
    # Not ours to validate: only the overlay key's own line is read; other lines are skipped.
    prefix = f"{OVERLAY_DIR_ENV}="
    found = ""
    for line in _lines(layer):
        line = line.strip()
        if line.startswith(prefix):
            value = line[len(prefix) :]
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            found = value  # last assignment wins, as with bash `. file`
    return Path(found).expanduser() if found else None


def overlay_dir() -> Path | None:
    """Resolve the overlay dir; None when the overlay is disabled or not configured."""
    value = os.environ.get(OVERLAY_DIR_ENV)
    if value is None:
        return _dotfiles_pointer()
    return Path(value).expanduser() if value else None


def read_setting(key: str) -> str:
    if value := os.environ.get(key):
        return value
    directory = overlay_dir()
    if directory is None:
        raise SystemExit(f"{key} unset: export it, or set {OVERLAY_DIR_ENV} to a dir whose {SETTINGS_FILE} sets it")
    path = directory / SETTINGS_FILE
    found = ""
    if path.is_file():
        for lineno, line in enumerate(_lines(path), start=1):
            if not line or line.startswith("#"):
                continue
            if not _LINE.fullmatch(line):
                # Never echo the line: it may hold a real value.
                raise SystemExit(
                    f"{path}:{lineno}: invalid settings line; expected KEY=value "
                    "with no whitespace, quotes, $, `, # or backslash in the value"
                )
            name, _, value = line.partition("=")
            if name == key:
                found = value  # last assignment wins, as with bash `. file`
    if found:
        return found
    raise SystemExit(f"{key} unset: export it or add {key}=<value> to {path}")
