"""Handle the database connection and operations within a context manager."""

from __future__ import annotations

import dataclasses
import enum
import os
import sqlite3
import threading

from .struclogger import get_logger

__all__ = [
    "ListItem",
    "ListPriority",
    "ListStore",
]


class ListPriority(enum.IntEnum):
    """An enumeration of list priorities."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclasses.dataclass(frozen=True)
class ListItem:
    """A list item that represents a row in the liststore table."""

    author: int
    created_at: int
    updated_at: int
    closed_at: int
    message_reference: int
    message: str
    priority: ListPriority


class ListStore:
    """Handle the database connection and operations within a context manager."""

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
        self._connection: sqlite3.Connection | None = None
        self._writer_lock: threading.Lock = threading.Lock()

    @property
    def connected(self) -> bool:
        """Return the connection status of the database."""
        return bool(self._connection)

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

        sqlite3.connect(database).close()
        liststore = cls(database)

        with liststore as store:
            store._logger.debug("Creating tables in database %s", database)
            store._create_tables()

        return liststore

    def _create_tables(self) -> None:
        """Create the table if it does not exist."""
        if not self._connection:
            raise sqlite3.Error("Database connection is closed.")

        with self._writer_lock:
            self._connection.execute(
                """\
                CREATE TABLE IF NOT EXISTS liststore (
                    row_id INTEGER PRIMARY KEY,
                    author INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    closed_at INTEGER,
                    message_reference INTEGER,
                    message TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 1
                );"""
            )
            self._connection.execute(
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
        if self._connection is not None:
            raise sqlite3.Error("Database connection already open.")

        self._connection = sqlite3.connect(self.database, check_same_thread=False)
        self._logger.debug("Opened database connection to %s", self.database)

        # If we are a memory database the tables need to be created for this connection.
        if self.database == ":memory:":
            self._logger.debug("Creating tables in memory database")
            self._create_tables()

    def close(self) -> None:
        """
        Close the database connection.

        Raises:
            sqlite3.Error: If the database connection is already closed.
        """
        if self._connection is None:
            raise sqlite3.Error("Database connection already closed.")

        self._connection.close()
        self._connection = None
        self._logger.debug("Closed database connection to %s", self.database)

    def write(self, item: ListItem) -> None:
        """
        Write an item to the database.

        This operation is a thread-safe write to the sqlite3 database. The
        operation is blocking until the item is written to the database.

        Args:
            item: The item to write to the database.

        Raises:
            sqlite3.Error: If the database connection is closed.
        """
        if not self._connection:
            raise sqlite3.Error("Database connection is closed.")

        with self._writer_lock:
            self._connection.execute(
                """\
                INSERT INTO liststore (
                    author,
                    created_at,
                    updated_at,
                    closed_at,
                    message_reference,
                    message,
                    priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(author, message_reference) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    closed_at = excluded.closed_at,
                    message = excluded.message,
                    priority = excluded.priority;
                """,
                (
                    item.author,
                    item.created_at,
                    item.updated_at,
                    item.closed_at,
                    item.message_reference,
                    item.message,
                    item.priority.value,
                ),
            )
            self._connection.commit()

    def __enter__(self) -> ListStore:
        """Context manager entry point."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        """Context manager exit point."""
        self.close()
