"""Database path resolution tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.database import DEFAULT_DB_PATH, ROOT, get_db_path


def test_get_db_path_default_is_repo_data_dir(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_db_path() == DEFAULT_DB_PATH
    assert get_db_path().parent == ROOT / "data"


def test_get_db_path_relative_sqlite_url_resolves_under_repo(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///data/setu.db")
    assert get_db_path() == ROOT / "data" / "setu.db"
    assert not str(get_db_path()).startswith("/data/")


def test_get_db_path_absolute_sqlite_url(monkeypatch, tmp_path):
    db_file = tmp_path / "absolute.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:////{db_file}")
    assert get_db_path() == db_file
    assert get_db_path().is_absolute()