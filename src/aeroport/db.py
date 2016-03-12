"""
Database interface. Very simple by now.
"""

import logging
import sqlite3

from sunhead.conf import settings

__all__ = ("sqlitedb",)

logger = logging.getLogger(__name__)


class SqliteDB(object):

    def __init__(self):
        self._db_path = settings.DB_PATH
        self._connection = None

    def connect(self) -> None:
        logger.info("Connecting sqlite db %s", self._db_path)
        self._connection = sqlite3.connect(self._db_path)

    def disconnect(self) -> None:
        if self._connection is not None:
            logger.info("Disconnecting sqlite db")
            self._connection.close()

    @property
    def connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    def ensure_tables(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              airline TEXT,
              origin TEXT,
              started TEXT,
              finished TEXT,
              num_processed INTEGER
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS airline_settings (
              airline TEXT,
              schedule TEXT,
              enabled INTEGER,
              targets TEXT
            )
            """
        )
        self.connection.commit()


sqlitedb = SqliteDB()
