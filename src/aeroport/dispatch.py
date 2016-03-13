"""
Direct operations and check what's in the air now.
"""

from datetime import datetime

from aeroport.abc import AbstractAirline, AbstractOrigin
from aeroport.db import sqlitedb


class Flight(object):

    STATUS_NEW = 0
    STATUS_IN_AIR = 1
    STATUS_LANDED = 2

    SAVE_ON_EACH = 10

    def __init__(self, airline: AbstractAirline, origin: AbstractOrigin):
        self._airline = airline
        self._origin = origin
        self._start_time = None
        self._start_time_iso = None
        self._finish_time = None
        self._finish_time_iso = None
        self._num_processed = None
        self._status = self.STATUS_NEW

    def start(self):
        self._start_time = datetime.now()
        self._start_time_iso = self._datetime_to_iso(self._start_time)
        self._status = self.STATUS_IN_AIR
        self._store_data()

    def finish(self, total_processed=None):
        self._finish_time = datetime.now()
        self._finish_time_iso = self._datetime_to_iso(self._start_time)
        self._status = self.STATUS_LANDED
        if total_processed is not None:
            self._num_processed = total_processed
        self._store_data()

    @property
    def num_processed(self):
        return self._num_processed

    @num_processed.setter
    def num_processed(self, value):
        self._num_processed = value
        if self._num_processed % self.SAVE_ON_EACH == 0:
            self._store_data()

    def _datetime_to_iso(self, d: datetime) -> str:
        isoformat = d.isoformat()
        return isoformat

    def _store_data(self):
        fields = ("airline", "origin", "started", "finished", "num_processed")
        values = (self._airline.name, self._origin.name, self._start_time_iso, self._finish_time_iso, self._num_processed)
        sqlitedb.set("flights", fields, values, "origin", self._origin.name)
