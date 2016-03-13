"""
HTTP server, providing Admin interface and some APIs.
"""

import asyncio
from functools import partial
import logging
import os

import aiocron

from sunhead.conf import settings
from sunhead.cli.banners import print_banner
from sunhead.workers.http.server import Server

from aeroport.db import sqlitedb
from aeroport import management
from aeroport.web.rest.urls import urlconf as rest_urlconf


logger = logging.getLogger(__name__)

REST_URL_PREFIX = "/api/1.0"


class AeroportHTTPServer(Server):

    @property
    def app_name(self):
        return "AeroportHTTPServer"

    def _map_to_prefix(self, urlprefix: str, urlconf: tuple) -> tuple:
        mapped = ((method, urlprefix + url, view) for method, url, view in urlconf)
        return tuple(mapped)

    def get_urlpatterns(self):
        urls = self._map_to_prefix(REST_URL_PREFIX, rest_urlconf)
        return urls

    def print_banner(self):
        filename = os.path.join(os.path.dirname(__file__), "templates", "logo.txt")
        print_banner(filename)
        super().print_banner()

    def init_requirements(self, loop):
        sqlitedb.set_db_path(settings.DB_PATH)
        sqlitedb.connect()
        sqlitedb.ensure_tables()
        self.set_timetable(loop)

    def cleanup(self, srv, handler, loop):
        sqlitedb.disconnect()
        # TODO: Kill all scraping and processing executors

    # TODO: Move to separate module, connect with airline schedule change API
    @property
    def timetable(self):
        if "timetable" not in self.app:
            self.app["timetable"] = {}
        return self.app["timetable"]

    def set_timetable(self, loop):
        for airline_info in management.get_airlines_list():
            airline = management.get_airline(airline_info.name)
            schedule = airline.get_schedule()
            for origin_name, crontab in schedule.items():
                self._set_origin_processing_crontab(airline.name, origin_name, crontab)

    def _set_origin_processing_crontab(self, airline_name: str, origin_name: str, crontab: str) -> None:
        key = "{}_{}".format(airline_name, origin_name)
        if key in self.timetable:
            self.timetable[key].stop()
        processor = partial(self._process_origin, airline_name, origin_name)
        schedule_executor = aiocron.crontab(crontab, processor, start=True)
        logger.debug("Scheduling airline=%s, origin=%s at '%s'", airline_name, origin_name, crontab)
        self.timetable["key"] = schedule_executor

    async def _process_origin(self, airline_name, origin_name: str) -> None:
        logger.info("Starting scheduled processing: airline=%s, origin=%s", airline_name, origin_name)
        airline = management.get_airline(airline_name)
        origin = airline.get_origin(origin_name)
        asyncio.ensure_future(
            origin.process()
        )
