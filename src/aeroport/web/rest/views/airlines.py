"""
Airline settings & info views.
"""

import asyncio

from aiohttp import web_exceptions

from sunhead.rest.views import JSONView

from aeroport import management
from aeroport.db import sqlitedb


class BaseAirlineView(JSONView):

    @property
    def requested_airline(self):
        return self.request.match_info.get("airline", None)

    @property
    def requested_origin(self):
        return self.request.match_info.get("origin", None)

    def json_response(self, context_data=None):
        context_data.update(
            {
                "requested_airline": self.requested_airline,
                "requested_origin": self.requested_origin,
            }
        )
        return super().json_response(context_data)


class AirlinesListView(BaseAirlineView):

    async def get(self):
        airlines_data = [
            {
                "name": airline.name,
                "module_path": airline.module_path
            } for airline in management.get_airlines_list()
        ]
        ctx = {
            "airlines": airlines_data,
        }
        return self.json_response(ctx)


class AirlineView(BaseAirlineView):

    async def get(self):
        airline = management.get_airline(self.requested_airline)
        origins_data = [
            {
                "name": origin.name,
                "module_path": origin.module_path
            } for origin in airline.get_origin_list()
        ]
        ctx = {
            "airline": {
                "name": airline.name,
                "title": airline.title,
            },
            "origins": origins_data,
            "enabled": True,
            "schedule": {},
            "targets": {},
        }
        return self.json_response(ctx)


class OriginView(BaseAirlineView):

    async def get(self):
        airline = management.get_airline(self.requested_airline)
        origin = airline.get_origin(self.requested_origin)
        ctx = {
            "airline": {
                "name": airline.name,
                "title": airline.title,
            },
            "origin": {
                "name": origin.__class__.__name__,
            },
            "schedule": {},
        }
        return self.json_response(ctx)
