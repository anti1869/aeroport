"""
HTTP server, providing Admin interface and some APIs.
"""

from functools import partial
from itertools import chain
import logging
import os

import aiocron

from sunhead.conf import settings
from sunhead.cli.banners import print_banner
from sunhead.metrics import get_metrics
from sunhead.workers.http.server import Server
from sunhead.workers.http.ext.runtime import ServerStatsMixin

from aeroport.management.utils import get_airlines_list, get_airline
from aeroport.dispatch import process_origin
from aeroport.web.rest.urls import urlconf as rest_urlconf


logger = logging.getLogger(__name__)


class AeroportHTTPServer(ServerStatsMixin, Server):

    @property
    def app_name(self):
        return "aeroport"

    def _map_to_prefix(self, urlprefix: str, urlconf: tuple) -> tuple:
        mapped = ((method, urlprefix + url, view) for method, url, view in urlconf)
        return tuple(mapped)

    def get_urlpatterns(self):
        super_urls = super().get_urlpatterns()
        urls = chain(super_urls, self._map_to_prefix(settings.REST_URL_PREFIX, rest_urlconf))
        return urls

    def print_banner(self):
        filename = os.path.join(os.path.dirname(__file__), "templates", "logo.txt")
        print_banner(filename)
        super().print_banner()

    def init_requirements(self, loop):
        metrics = get_metrics()
        metrics.app_name_prefix = self.app_name

        super().init_requirements(loop)
        loop.run_until_complete(self.set_timetable(loop))

    def cleanup(self, srv, handler, loop):
        # TODO: Kill all scraping and processing executors
        pass

    # TODO: Move to separate module, connect with airline schedule change API
    @property
    def timetable(self):
        if "timetable" not in self.app:
            self.app["timetable"] = {}
        return self.app["timetable"]

    async def set_timetable(self, loop):
        for airline_info in get_airlines_list():
            airline = get_airline(airline_info.name)
            schedule = await airline.get_schedule()
            for origin_name, entries in schedule.items():
                for entry in entries:
                    destination = entry.get("destination", None)
                    crontab = entry.get("crontab", None)
                    if not crontab:
                        continue
                    self._set_origin_processing_crontab(airline.name, origin_name, destination, crontab)

    def _set_origin_processing_crontab(self, airline_name: str, origin_name: str, destination: str, crontab: str):
        key = "{}_{}_{}".format(airline_name, origin_name, destination)
        if key in self.timetable:
            self.timetable[key].stop()
        processor = partial(self._process_origin, airline_name, origin_name, destination)
        schedule_executor = aiocron.crontab(crontab, processor, start=True)
        logger.debug(
            "Scheduling airline=%s, origin=%s, destination=%s at '%s'",
            airline_name, origin_name, destination, crontab
        )
        self.timetable["key"] = schedule_executor

    async def _process_origin(self, airline_name, origin_name, destination_name):
        logger.info(
            "Starting scheduled processing: airline=%s, origin=%s, destination=%s",
            airline_name,
            origin_name,
            destination_name
        )
        await process_origin(airline_name, origin_name, destination_name)
