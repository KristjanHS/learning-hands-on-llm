from __future__ import annotations

import re
from pathlib import Path

import pytest

from phase1.python_code import overlay_settings
from phase1.python_code.overlay_settings import (
    DOTFILES_DIR_ENV,
    DOTFILES_LAYER,
    OVERLAY_DIR_ENV,
    SETTINGS_FILE,
    overlay_dir,
    read_setting,
)

KEY = "EXAMPLE_HOST"


@pytest.fixture
def overlay(tmp_path, monkeypatch):
    monkeypatch.setenv(OVERLAY_DIR_ENV, str(tmp_path))
    monkeypatch.delenv(KEY, raising=False)
    return tmp_path


@pytest.fixture
def no_overlay_env(monkeypatch):
    monkeypatch.delenv(OVERLAY_DIR_ENV, raising=False)
    monkeypatch.delenv(KEY, raising=False)


def _dotfiles_with_pointer(root: Path, line: str) -> Path:
    layer = root / "dotfiles" / DOTFILES_LAYER
    layer.parent.mkdir(parents=True)
    layer.write_text(f"# shared layer\nOTHER_KEY=1\nQUOTED='a b'\n{line}\n")
    return root / "dotfiles"


def test_overlay_present_returns_value(overlay):
    (overlay / SETTINGS_FILE).write_text(f"# {KEY}=commented.example\n{KEY}=real.example\n")
    assert read_setting(KEY) == "real.example"


def test_env_wins_over_overlay(overlay, monkeypatch):
    (overlay / SETTINGS_FILE).write_text(f"{KEY}=real.example\n")
    monkeypatch.setenv(KEY, "tmp.example")
    assert read_setting(KEY) == "tmp.example"


def test_repeated_key_last_wins(overlay):
    (overlay / SETTINGS_FILE).write_text(f"{KEY}=first.example\n{KEY}=second.example\n")
    assert read_setting(KEY) == "second.example"


def test_utf8_bom_ignored(overlay):
    (overlay / SETTINGS_FILE).write_text(f"﻿{KEY}=real.example\n", encoding="utf-8")
    assert read_setting(KEY) == "real.example"


def test_empty_file_value_exits(overlay):
    (overlay / SETTINGS_FILE).write_text(f"{KEY}=\n")
    with pytest.raises(SystemExit, match=f"{KEY} unset"):
        read_setting(KEY)


def test_overlay_file_absent_exits_with_named_key(overlay):
    with pytest.raises(SystemExit, match=rf"{KEY} unset: .*{re.escape(SETTINGS_FILE)}"):
        read_setting(KEY)


@pytest.mark.parametrize(
    "bad_line",
    [
        f"{KEY}=secretvalue ",
        f"export {KEY}=secretvalue",
        f'{KEY}="secretvalue"',
        f"{KEY}=$secretvalue",
        f"{KEY}=secretvalue # c",
    ],
    ids=["trailing-space", "export", "double-quotes", "dollar", "inline-comment"],
)
def test_forbidden_line_rejected_with_location_not_value(overlay, bad_line):
    path = overlay / SETTINGS_FILE
    path.write_text(f"# header\nOTHER=ok\n{bad_line}\n")
    with pytest.raises(SystemExit) as excinfo:
        read_setting(KEY)
    message = str(excinfo.value)
    assert f"{path}:3:" in message
    assert "secretvalue" not in message


def test_crlf_and_bom_accepted(overlay):
    (overlay / SETTINGS_FILE).write_bytes(f"﻿# c\r\n{KEY}=real.example\r\n\r\n".encode())
    assert read_setting(KEY) == "real.example"


def test_last_key_wins_across_other_keys(overlay):
    (overlay / SETTINGS_FILE).write_text(f"{KEY}=first.example\nOTHER=x\n{KEY}=third.example\n")
    assert read_setting(KEY) == "third.example"


def test_env_overlay_dir_wins_over_dotfiles_pointer(tmp_path, monkeypatch):
    dotfiles = _dotfiles_with_pointer(tmp_path, f"{OVERLAY_DIR_ENV}=/from/pointer")
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(dotfiles))
    monkeypatch.setenv(OVERLAY_DIR_ENV, "/from/env")
    assert overlay_dir() == Path("/from/env")


def test_empty_env_disables_even_with_pointer(tmp_path, monkeypatch, no_overlay_env):
    dotfiles = _dotfiles_with_pointer(tmp_path, f"{OVERLAY_DIR_ENV}=/from/pointer")
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(dotfiles))
    monkeypatch.setenv(OVERLAY_DIR_ENV, "")
    assert overlay_dir() is None
    with pytest.raises(SystemExit, match=f"{KEY} unset: export it, or set {OVERLAY_DIR_ENV}"):
        read_setting(KEY)


def test_unset_env_follows_dotfiles_pointer(tmp_path, monkeypatch, no_overlay_env):
    dotfiles = _dotfiles_with_pointer(tmp_path, f"{OVERLAY_DIR_ENV}=/first\n{OVERLAY_DIR_ENV}='/from/pointer'")
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(dotfiles))
    assert overlay_dir() == Path("/from/pointer")


def test_unset_env_without_pointer_or_layer_means_no_overlay(tmp_path, monkeypatch, no_overlay_env):
    dotfiles = _dotfiles_with_pointer(tmp_path, "UNRELATED=x")
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(dotfiles))
    assert overlay_dir() is None
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(tmp_path / "absent"))
    assert overlay_dir() is None
    with pytest.raises(SystemExit, match=f"{KEY} unset: export it, or set {OVERLAY_DIR_ENV}"):
        read_setting(KEY)


def test_unset_env_reads_value_from_overlay_named_by_pointer(tmp_path, monkeypatch, no_overlay_env):
    target = tmp_path / "overlay"
    target.mkdir()
    (target / SETTINGS_FILE).write_text(f"{KEY}=pointed.example\n")
    dotfiles = _dotfiles_with_pointer(tmp_path, f"{OVERLAY_DIR_ENV}={target}")
    monkeypatch.setenv(DOTFILES_DIR_ENV, str(dotfiles))
    assert read_setting(KEY) == "pointed.example"


def test_default_dotfiles_dir_sits_beside_the_main_checkout(tmp_path, monkeypatch, no_overlay_env):
    _dotfiles_with_pointer(tmp_path, f"{OVERLAY_DIR_ENV}=/from/pointer")
    monkeypatch.delenv(DOTFILES_DIR_ENV, raising=False)
    monkeypatch.setattr(overlay_settings, "_main_root", lambda: tmp_path / "repo")
    assert overlay_dir() == Path("/from/pointer")


def test_main_root_is_the_main_checkout():
    root = overlay_settings._main_root()
    assert (root / "phase1" / "python_code" / "overlay_settings.py").is_file()
