"""Runtime settings: env var, else `$LEARNING_HANDS_ON_LLM_OVERLAY_DIR/settings.env` (KEY=value lines)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

OVERLAY_DIR_ENV = "LEARNING_HANDS_ON_LLM_OVERLAY_DIR"
OVERLAY_NAME = "learning-hands-on-llm-overlay"
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


def overlay_dir() -> Path:
    override = os.environ.get(OVERLAY_DIR_ENV)
    return Path(override) if override else _main_root().parent / OVERLAY_NAME


def read_setting(key: str) -> str:
    if value := os.environ.get(key):
        return value
    path = overlay_dir() / "settings.env"
    found = ""
    if path.is_file():
        # Bytes, not read_text: universal newlines would also split on a lone CR, which
        # the bash reader does not. utf-8-sig tolerates a leading BOM.
        text = path.read_bytes().decode("utf-8-sig")
        for lineno, raw in enumerate(text.split("\n"), start=1):
            line = raw.removesuffix("\r")  # tolerate CRLF
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
