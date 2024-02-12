"""Handle the database connection and operations within a context manager."""

from __future__ import annotations

import dataclasses
import os
import sqlite3
import threading
from queue import Empty
from queue import Queue

from .struclogger import get_logger


@dataclasses.dataclass(frozen=True)
class ListItem:
    """A list item that represents a row in the liststore table."""

    author: int
    created_at: int
    updated_at: int
    closed_at: int
    message_reference: int
    message: str


class ListStore:
    """Handle the database connection and operations within a context manager."""

    # Keep the queue timeout low to allow for quick shutdown but not too low to cause
    # excessive CPU usage in the writer thread.
    QUEUE_TIMEOUT = 0.5
    _logger = get_logger(__name__)

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
        self._connected = False
        self._reader: sqlite3.Connection | None = None
        self._writer = threading.Thread()
        self._writer_queue: Queue[ListItem] = Queue()

    @property
    def connected(self) -> bool:
        """Return the connection status of the database."""
        return self._connected

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
            ListStore._logger.debug("Creating tables in database %s", database)
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
            CREATE UNIQUE INDEX IF NOT EXISTS
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
        self._connected = True
        self._logger.debug("Opened database connection to %s", self.database)

        # If we are a memory database the tables need to be created for this connection.
        if self.database == ":memory:":
            self._logger.debug("Creating tables in memory database")
            self._create_tables(self._reader)

        # Create a writer thread to handle asynchronous processes wanting to write to the database.
        self._logger.debug("Starting writer thread")
        self._writer = threading.Thread(target=self._writer_thread)
        self._writer.start()
        self._logger.debug("Started writer thread")

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
        self._connected = False
        self._logger.debug("Closed database connection to %s", self.database)
        self._logger.debug("Waiting for writer thread to finish...")
        self._writer.join()
        self._logger.debug("Writer thread finished and closed.")

    def write(self, item: ListItem) -> None:
        """
        Write an item to the database.

        This operates as a non-blocking operation and will queue the item for
        writing. The item will be created or updated in the database based on
        the message_reference and author.

        Args:
            item: The item to write to the database.

        Raises:
            sqlite3.Error: If the database connection is closed.
        """
        if not self.connected:
            raise sqlite3.Error("Database connection is closed.")
        self._writer_queue.put(item)
        self._logger.debug(
            "Queued item for writing. %s, %s, %s",
            item.author,
            item.message_reference,
            item.message,
        )

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

            while "On a dark desert highway, cool wind in my hair":
                try:
                    item = self._writer_queue.get(timeout=self.QUEUE_TIMEOUT)
                    self._logger.debug(
                        "Writing to database. %s, %s",
                        item.author,
                        item.message_reference,
                    )
                    self._write_row(item, connection)

                except Empty:
                    if not self.connected:
                        break

        finally:
            connection.close()

    def _write_row(self, item: ListItem, connection: sqlite3.Connection) -> None:
        """Write a row to the database."""
        connection.execute(
            """\
            INSERT INTO liststore (
                author,
                created_at,
                updated_at,
                closed_at,
                message_reference,
                message
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(author, message_reference) DO UPDATE SET
                updated_at = excluded.updated_at,
                closed_at = excluded.closed_at,
                message = excluded.message;
            """,
            (
                item.author,
                item.created_at,
                item.updated_at,
                item.closed_at,
                item.message_reference,
                item.message,
            ),
        )
        connection.commit()
