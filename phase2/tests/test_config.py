"""Smoke test: verify phase2 RAG_app modules are importable."""

from __future__ import annotations


def test_config_constants():
    from phase2.RAG_app.config import CHUNK_SIZE, COLLECTION_NAME

    assert isinstance(COLLECTION_NAME, str)
    assert CHUNK_SIZE > 0
