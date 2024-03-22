from __future__ import annotations

import os
import sqlite3
import threading

import pytest

from objeggtives.liststore import ListItem
from objeggtives.liststore import ListPriority
from objeggtives.liststore import ListStore
from objeggtives.liststore import get_liststore


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


def test_create_tables_requires_connection() -> None:
    liststore = ListStore(":memory:")
    with pytest.raises(sqlite3.Error):
        liststore._create_tables()


def test_open_with_context_manager_from_file(tmpdir) -> None:
    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        assert liststore.connected is True
        assert liststore._connection is not None
        assert _has_table(liststore._connection, "liststore") is True

    assert liststore._connection is None


def test_open_with_context_manager_from_memory() -> None:
    with ListStore(":memory:") as liststore:
        assert liststore.connected is True
        assert liststore._connection is not None
        assert _has_table(liststore._connection, "liststore") is True

    assert liststore._connection is None


def test_get_liststore_creates_new_file(tmpdir) -> None:
    tempfile = tmpdir.join("test.db")
    get_liststore(tempfile)

    assert os.path.exists(tempfile)


def test_open_using_get_liststore_twice_gives_same_connection() -> None:
    first_liststore = get_liststore(":memory:")
    with first_liststore as store_one:
        expected_id = id(store_one._connection)

        second_liststore = get_liststore(":memory:")
        with second_liststore as store_two:

            assert id(store_two._connection) == expected_id


def test_write_row_to_database(tmpdir) -> None:
    write_one = ListItem(1, 2, 3, 0, 5, "message", ListPriority.LOW)
    write_two = ListItem(1, 2, 3, 0, 6, "other message", ListPriority.HIGH)

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
        assert rows[0] == (1, 1, 2, 3, 0, 5, "message", 1)
        assert rows[1] == (2, 1, 2, 3, 0, 6, "other message", 3)


def test_write_row_to_database_with_update(tmpdir) -> None:
    write_one = ListItem(1, 2, 3, 0, 5, "message", ListPriority.LOW)
    write_two = ListItem(1, 2, 8, 9, 5, "new message", ListPriority.HIGH)

    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        liststore.write(write_one)
        liststore.write(write_two)

    with sqlite3.connect(tempfile) as conn:
        cursor = conn.execute("SELECT * FROM liststore")
        rows = cursor.fetchall()

        assert len(rows) == 1
        # Extra 1 here to account for the rowid
        assert rows[0] == (1, 1, 2, 8, 9, 5, "new message", 3)


def test_write_with_open_connection() -> None:
    liststore = ListStore(":memory:")

    with pytest.raises(sqlite3.Error):
        liststore.write(ListItem(1, 2, 3, 0, 5, "message", ListPriority.LOW))


def test_counts_with_closed_connection() -> None:
    liststore = ListStore(":memory:")

    with pytest.raises(sqlite3.Error):
        liststore.counts()


def test_counts_returns_correct_values() -> None:
    liststore = ListStore(":memory:")

    with liststore as store:
        store.write(ListItem(1, 2, 3, 0, 5, "message", ListPriority.LOW))
        store.write(ListItem(1, 2, 3, 1, 6, "other message", ListPriority.HIGH))

        total, closed = store.counts()

    assert total == 2
    assert closed == 1


def _write_to_liststore(
    liststore: ListStore,
    rows_to_write: int,
    thread_number: int,
    start_flag: threading.Event,
) -> None:
    start_flag.wait()
    for idx in range(rows_to_write):
        liststore.write(ListItem(thread_number, 2, 3, 0, idx, "foo", ListPriority.LOW))


def test_write_to_liststore_with_locking(tmpdir) -> None:
    number_of_threads = 10
    rows_to_write = 60
    tempfile = tmpdir.join("test.db")
    ListStore.initialize(tempfile)

    with ListStore(tempfile) as liststore:
        threads = []
        start_flag = threading.Event()

        for thread_number in range(number_of_threads):
            args = (liststore, rows_to_write, thread_number, start_flag)
            thread = threading.Thread(target=_write_to_liststore, args=args)
            threads.append(thread)
            thread.start()

        start_flag.set()

        for thread in threads:
            thread.join()

    with sqlite3.connect(tempfile) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM liststore")
        rows = cursor.fetchall()

    os.remove(tempfile)

    assert len(rows) == number_of_threads * rows_to_write
