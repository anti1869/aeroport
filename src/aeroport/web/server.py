"""
HTTP server, providing Admin interface and some APIs.
"""

import os

from sunhead.cli.banners import print_banner
from sunhead.workers.http.server import Server

from aeroport.web.rest.urls import urlconf as rest_urlconf


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
