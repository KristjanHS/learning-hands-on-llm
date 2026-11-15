"""Runtime settings: env var, else `$LEARNING_HANDS_ON_LLM_OVERLAY_DIR/settings.env` (KEY=value lines)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

OVERLAY_DIR_ENV = "LEARNING_HANDS_ON_LLM_OVERLAY_DIR"
OVERLAY_NAME = "learning-hands-on-llm-overlay"


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
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            name, _, value = line.partition("=")
            if name == key:
                found = value  # last assignment wins, as with bash `. file`
    if found:
        return found
    raise SystemExit(f"{key} unset: export it or add {key}=<value> to {path}")
