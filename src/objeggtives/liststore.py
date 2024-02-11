"""
Handle the database connection and operations within a context manager.

[] - Open the database connection
[] - Close the database connection
[x] - Create database and tables if it does not exist
[] - Start writer thread (should use its own connection)
[] - Method for writing to the database
"""

from __future__ import annotations

import os
import sqlite3


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
                id INTEGER PRIMARY KEY,
                author INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                closed_at INTEGER,
                message_reference INTEGER,
                message TEXT NOT NULL
            );"""
        )
