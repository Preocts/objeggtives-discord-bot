from __future__ import annotations

import sqlite3
import time

import pytest

from objeggtives.liststore import ListItem
from objeggtives.liststore import ListStore


def _has_table(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


def test_initialize_liststore_file_exists_error(tmpdir) -> None:
    database = tmpdir.join("test.db")
    database.write("")

    with pytest.raises(FileExistsError):
        ListStore.initialize(database)


def test_initialize_liststore_create_tables(tmpdir) -> None:
    tempfile = tmpdir.join("test.db")

    liststore = ListStore.initialize(tempfile)

    with sqlite3.connect(liststore.database) as conn:
        assert _has_table(conn, "liststore") is True


def test_raise_file_not_found_on_init() -> None:
    with pytest.raises(FileNotFoundError):
        ListStore("thisfiledoesnotexist.db")


def test_allow_memory_database() -> None:
    ListStore(":memory:")


def test_open_with_context_manager_from_file(tmpdir) -> None:
    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        assert liststore._reader is not None
        assert _has_table(liststore._reader, "liststore") is True

    assert liststore._reader is None


def test_open_with_context_manager_from_memory() -> None:
    with ListStore(":memory:") as liststore:
        assert liststore._reader is not None
        assert _has_table(liststore._reader, "liststore") is True

    assert liststore._reader is None


def test_open_twice_raises_error() -> None:
    with ListStore(":memory:") as liststore:
        with pytest.raises(sqlite3.Error):
            liststore.open()


def test_close_twice_raises_error() -> None:
    liststore = ListStore(":memory:")
    liststore.open()
    liststore.close()

    with pytest.raises(sqlite3.Error):
        liststore.close()


def test_write_row_to_database(tmpdir) -> None:
    write_one = ListItem(1, 2, 3, 0, 5, "message")
    write_two = ListItem(1, 2, 3, 0, 6, "other message")

    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        liststore.write(write_one)
        liststore.write(write_two)

    with sqlite3.connect(tempfile) as conn:
        cursor = conn.execute("SELECT * FROM liststore")
        rows = cursor.fetchall()

        assert len(rows) == 2

        # rowid needs to be included in the comparison
        assert rows[0] == (1, 1, 2, 3, 0, 5, "message")
        assert rows[1] == (2, 1, 2, 3, 0, 6, "other message")


def test_write_row_to_database_with_update(tmpdir) -> None:
    write_one = ListItem(1, 2, 3, 0, 5, "message")
    write_two = ListItem(1, 2, 8, 9, 5, "new message")

    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        liststore.write(write_one)
        # Sleep here to ensure our writer thread is looping properly
        # This is for coverage purposes only
        time.sleep(1)
        liststore.write(write_two)

    with sqlite3.connect(tempfile) as conn:
        cursor = conn.execute("SELECT * FROM liststore")
        rows = cursor.fetchall()

        assert len(rows) == 1
        # Extra 1 here to account for the rowid
        assert rows[0] == (1, 1, 2, 8, 9, 5, "new message")


def test_write_with_open_connection() -> None:
    liststore = ListStore(":memory:")

    with pytest.raises(sqlite3.Error):
        liststore.write(ListItem(1, 2, 3, 0, 5, "message"))
