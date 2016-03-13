"""
Database interface. Very simple by now.
"""

from collections import Sequence
import logging
import sqlite3

import simplejson as json

__all__ = ("sqlitedb",)

logger = logging.getLogger(__name__)


# TODO: Whole this stuff is likely to be trashed, as it is actually a complete shit.

class SqliteDB(object):

    def __init__(self):
        self._db_path = None
        self._connection = None

    def set_db_path(self, db_path: str) -> None:
        self._db_path = db_path

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
            CREATE TABLE IF NOT EXISTS flights (
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

    def to_json(self, data) -> str:
        json_encoded = json.dumps(data)
        return json_encoded

    def from_json(self, serialized: str):
        data = json.loads(serialized)
        return data

    def get(self, table, field_name, cond_field, cond_value, default):
        cursor = self.connection.cursor()
        q = 'SELECT {} FROM {} WHERE {} = ?'.format(field_name, table, cond_field)
        cursor.execute(q, (cond_value,))
        try:
            result = cursor.fetchone()[0]
        except TypeError:
            result = default
        return result

    def set(self, table, field_names, values, cond_field, cond_value):

        # Convert to sequences if needed
        field_names, values = map(lambda x: (x,) if not isinstance(x, (list, tuple)) else x, (field_names, values))
        set_portion = ",".join(("{} = ?".format(name) for name in field_names))

        cursor = self.connection.cursor()
        self._ensure_record(cursor, table, cond_field, cond_value)
        q = "UPDATE {} SET {} WHERE {} = ?".format(table, set_portion, cond_field)
        cursor.execute(q, values + (cond_value, ))
        self.connection.commit()

    def _ensure_record(self, cursor, table, cond_field, cond_value):
        q = 'SELECT ROWID FROM {} WHERE {} = ?'.format(table, cond_field)
        cursor.execute(q, (cond_value,))
        result = cursor.fetchone()

        if result is None:
            q = "INSERT INTO {} ({}) VALUES (?)".format(table, cond_field)
            cursor.execute(q, (cond_value, ))


sqlitedb = SqliteDB()
