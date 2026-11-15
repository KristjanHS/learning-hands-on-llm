from __future__ import annotations

import pytest

from phase1.python_code import overlay_settings
from phase1.python_code.overlay_settings import OVERLAY_DIR_ENV, read_setting


@pytest.fixture
def companion(tmp_path, monkeypatch):
    monkeypatch.setenv(OVERLAY_DIR_ENV, str(tmp_path))
    monkeypatch.delenv("NGROK_DOMAIN", raising=False)
    return tmp_path


def test_companion_present_returns_value(companion):
    (companion / "settings.env").write_text("# NGROK_DOMAIN=commented.example\nNGROK_DOMAIN=real.example\n")
    assert read_setting("NGROK_DOMAIN") == "real.example"


def test_env_wins_over_companion(companion, monkeypatch):
    (companion / "settings.env").write_text("NGROK_DOMAIN=real.example\n")
    monkeypatch.setenv("NGROK_DOMAIN", "tmp.example")
    assert read_setting("NGROK_DOMAIN") == "tmp.example"


def test_repeated_key_last_wins(companion):
    (companion / "settings.env").write_text("NGROK_DOMAIN=first.example\nNGROK_DOMAIN=second.example\n")
    assert read_setting("NGROK_DOMAIN") == "second.example"


def test_utf8_bom_ignored(companion):
    (companion / "settings.env").write_text("﻿NGROK_DOMAIN=real.example\n", encoding="utf-8")
    assert read_setting("NGROK_DOMAIN") == "real.example"


def test_empty_file_value_exits(companion):
    (companion / "settings.env").write_text("NGROK_DOMAIN=\n")
    with pytest.raises(SystemExit, match="NGROK_DOMAIN unset"):
        read_setting("NGROK_DOMAIN")


def test_companion_absent_exits_with_named_key(companion):
    with pytest.raises(SystemExit, match=r"NGROK_DOMAIN unset: .*settings\.env"):
        read_setting("NGROK_DOMAIN")


def test_default_overlay_dir_is_sibling_of_main_checkout(monkeypatch):
    monkeypatch.delenv(OVERLAY_DIR_ENV, raising=False)
    root = overlay_settings._main_root()
    assert (root / "phase1" / "python_code" / "overlay_settings.py").is_file()
    assert overlay_settings.overlay_dir() == root.parent / "learning-hands-on-llm-overlay"
