from __future__ import annotations

import sqlite3

import pytest

from objeggtives.liststore import ListStore


def test_initialize_liststore_file_exists_error(tmpdir) -> None:
    database = tmpdir.join("test.db")
    database.write("")

    with pytest.raises(FileExistsError):
        ListStore.initialize(database)


def test_initialize_liststore_create_tables(tmpdir) -> None:
    tempfile = tmpdir.join("test.db")

    liststore = ListStore.initialize(tempfile)

    with sqlite3.connect(liststore.database) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='liststore'"
        )
        assert cursor.fetchone() is not None


def test_raise_file_not_found_on_init() -> None:
    with pytest.raises(FileNotFoundError):
        ListStore("thisfiledoesnotexist.db")


def test_allow_memory_database() -> None:
    ListStore(":memory:")
