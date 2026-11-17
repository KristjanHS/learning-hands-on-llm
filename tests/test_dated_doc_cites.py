"""Guard: every cited dated doc (``YYYY-MM-DD-<slug>.md``) must resolve to a tracked file.

A dated doc that gets deleted or renamed while other files still cite it leaves a
dangling reference. This test scans every tracked text file for dated ``.md`` cites
and fails on any whose basename is not a tracked file, minus the pinned baseline.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CITE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[\w.-]+\.md")

# Dangling cites accepted today (basename of the cited doc). Shrink it; never grow it.
BASELINE_DANGLES: frozenset[str] = frozenset()


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    return [p for p in out.decode().split("\0") if p]


def _dangling_cites() -> dict[str, list[str]]:
    tracked = _tracked_files()
    tracked_names = {Path(p).name for p in tracked}
    dangles: dict[str, list[str]] = {}
    for rel in tracked:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:  # binary
            continue
        for cite in set(CITE_RE.findall(data.decode("utf-8", errors="replace"))):
            if cite not in tracked_names and cite not in BASELINE_DANGLES:
                dangles.setdefault(cite, []).append(rel)
    return dangles


def test_dated_doc_cites_resolve():
    dangles = _dangling_cites()
    assert not dangles, "dated doc cites with no tracked target: " + "; ".join(
        f"{cite} <- {', '.join(sorted(srcs))}" for cite, srcs in sorted(dangles.items())
    )
