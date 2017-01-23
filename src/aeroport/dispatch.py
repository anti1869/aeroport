"""
Direct operations and check what's in the air now.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
import uuid

import peewee

from aeroport.abc import AbstractOrigin
from aeroport.db import BaseModel, choices_from_enum
from aeroport.management.utils import get_airline
from aeroport.destinations.models import Destination


logger = logging.getLogger(__name__)


class ProcessingException(Exception):
    """Something wrong with processing"""


class FlightStatuses(Enum):
    new = 0
    in_air = 1
    landed = 2


# TODO: Add destination


class FlightRecord(BaseModel):
    """
    Persistent layer for flight records
    """
    airline = peewee.CharField()
    origin = peewee.CharField(index=True)
    status = peewee.IntegerField(choices=choices_from_enum(FlightStatuses))
    started = peewee.DateTimeField(null=True, index=True)
    finished = peewee.DateTimeField(null=True, index=True)
    num_processed = peewee.IntegerField(null=True)
    uuid = peewee.UUIDField()


class Flight(object):

    SAVE_ON_EACH = 10

    def __init__(self, origin: AbstractOrigin):
        self._airline = origin.airline
        self._origin = origin
        self._start_time = None
        self._start_time_iso = None
        self._finish_time = None
        self._finish_time_iso = None
        self._num_processed = None
        self._status = FlightStatuses.new
        self._flight_record = None

        self.uuid = uuid.uuid4()

    async def start(self):
        self._start_time = datetime.now()
        self._start_time_iso = self._datetime_to_iso(self._start_time)
        self._status = FlightStatuses.in_air
        await self._store_data()

    async def finish(self, total_processed=None):
        self._finish_time = datetime.now()
        self._finish_time_iso = self._datetime_to_iso(self._start_time)
        self._status = FlightStatuses.landed
        if total_processed is not None:
            self._num_processed = total_processed
        await self._store_data()

    @property
    def num_processed(self):
        return self._num_processed

    async def set_num_processed(self, value):
        self._num_processed = value
        if self._num_processed % self.SAVE_ON_EACH == 0:
            await self._store_data()

    def _datetime_to_iso(self, d: datetime) -> str:
        isoformat = d.isoformat()
        return isoformat

    async def _get_flight_record(self):
        if self._flight_record is None:
            self._flight_record, _ = await FlightRecord.db_manager.get_or_create(
                FlightRecord,
                {
                    "airline": self._airline.name,
                    "origin": self._origin.name,
                    "status": FlightStatuses.new.value,
                },
                uuid=self.uuid
            )
        return self._flight_record

    async def _store_data(self):
        flight_record = await self._get_flight_record()
        flight_record.started = self._start_time
        flight_record.finished = self._finish_time
        flight_record.num_processed = self.num_processed
        flight_record.status = self._status.value
        await FlightRecord.db_manager.update(flight_record)


async def process_origin(
        airline_name: str, origin_name: str, destination_name: str, use_await=False, **options):

    airline = get_airline(airline_name)
    origin = airline.get_origin(origin_name)
    origin.set_options(**options)

    if destination_name:
        try:
            dest = await Destination.db_manager.get(
                Destination, enabled=True, name=destination_name
            )
        except Destination.DoesNotExist:
            logger.error("There is not destination named '%s'" % destination_name)
            raise ProcessingException
        else:
            await origin.set_destination(dest.class_name, **dest.settings)

    if use_await:
        await origin.process()
    else:
        asyncio.ensure_future(origin.process())
