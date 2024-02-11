"""
Handle the database connection and operations within a context manager.

[x] - Open the database connection
[x] - Close the database connection
[x] - Create database and tables if it does not exist
[x] - Start writer thread (should use its own connection)
[] - Method for writing to the database
"""

from __future__ import annotations

import dataclasses
import os
import sqlite3
import threading
from queue import Empty
from queue import Queue


@dataclasses.dataclass(frozen=True)
class ListItem:
    """A list item that represents a row in the liststore table."""

    row_id: int
    author: int
    created_at: int
    updated_at: int
    closed_at: int
    message_reference: int
    message: str


class ListStore:
    """Handle the database connection and operations within a context manager."""

    def __init__(self, database: str) -> None:
        """
        Initialize the ListStore object.

        Use ListStore.Initialize() to create the database file if it does not exist.

        Args:
            database: The path to the sqlite3 database file. Use :memory: for an in-memory database.

        Raises:
            FileNotFoundError: If the database file does not exist.
        """
        if database != ":memory:" and not os.path.exists(database):
            raise FileNotFoundError(f"Database file {database} does not exist.")

        self.database = database
        self.connected = False
        self._reader: sqlite3.Connection | None = None
        self._writer = threading.Thread()
        self._writer_queue: Queue[ListItem] = Queue()

    @classmethod
    def initialize(cls, database: str) -> ListStore:
        """
        Create the database file and return a new ListStore object.

        Args:
            database: The path to the sqlite3 database file. Use :memory: for an in-memory database.

        Raises:
            FileExistsError: If the database file already exists.
        """
        if database != ":memory:" and os.path.exists(database):
            raise FileExistsError(f"Database file {database} already exists.")

        with sqlite3.connect(database) as conn:
            ListStore._create_tables(conn)

        return cls(database)

    @staticmethod
    def _create_tables(conn: sqlite3.Connection) -> None:
        """Create the table if it does not exist."""
        conn.execute(
            """\
            CREATE TABLE IF NOT EXISTS liststore (
                row_id INTEGER PRIMARY KEY,
                author INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                closed_at INTEGER,
                message_reference INTEGER,
                message TEXT NOT NULL
            );"""
        )
        conn.execute(
            """\
            CREATE INDEX IF NOT EXISTS
                idx_row
            ON
                liststore (author, message_reference);
            """
        )

    def open(self) -> None:  # noqa: A003 # Allow shadowing of built-in 'open'
        """
        Open the database connection.

        Returns:
            The ListStore object.

        Raises:
            sqlite3.Error: If the database connection cannot be established.
        """
        if self._reader is not None:
            raise sqlite3.Error("Database connection already open.")

        self._reader = sqlite3.connect(self.database)
        self.connected = True

        # If we are a memory database the tables need to be created for this connection.
        if self.database == ":memory:":
            self._create_tables(self._reader)

        # Create a writer thread to handle asynchronous processes wanting to write to the database.
        self._writer = threading.Thread(target=self._writer_thread)
        self._writer.start()

    def close(self) -> None:
        """
        Close the database connection.

        Raises:
            sqlite3.Error: If the database connection is already closed.
        """
        if self._reader is None:
            raise sqlite3.Error("Database connection already closed.")

        self._reader.close()
        self._reader = None
        self.connected = False
        self._writer.join()

    def __enter__(self) -> ListStore:
        """Context manager entry point."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Context manager exit point."""
        self.close()

    def _writer_thread(self) -> None:
        """Thread target for writing to the database."""
        try:
            connection = sqlite3.connect(self.database)

            while self.connected:
                try:
                    item = self._writer_queue.get(timeout=0.5)
                    print("Writing to database: ", item)
                    # self._write_to_database(connection, item)

                except Empty:
                    continue

        finally:
            connection.close()
