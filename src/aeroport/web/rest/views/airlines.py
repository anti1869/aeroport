"""
Airline settings & info views.
"""

from aiohttp import web_exceptions
import simplejson as json

from sunhead.rest.views import JSONView

from aeroport.management.utils import get_airlines_list, get_airline


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
            } for airline in get_airlines_list()
        ]
        ctx = {
            "airlines": airlines_data,
        }
        return self.json_response(ctx)


class AirlineView(BaseAirlineView):

    async def get(self):
        airline = get_airline(self.requested_airline)
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
            "enabled": await airline.is_enabled(),
            "schedule": await airline.get_schedule(),
            "targets": {},
        }
        return self.json_response(ctx)

    async def put(self):
        airline = get_airline(self.requested_airline)
        data = await self.request.post()
        schedule_json = data.get("schedule", None)
        if schedule_json is not None:
            schedule = json.loads(schedule_json)
            await airline.set_schedule(schedule)

        enabled = data.get("enabled", None)
        if enabled is not None:
            value = str(enabled).lower() in {"true", "1"}
            await airline.set_is_enabled(value)

        raise web_exceptions.HTTPNoContent


class OriginView(BaseAirlineView):

    async def get(self):
        airline = get_airline(self.requested_airline)
        origin = airline.get_origin(self.requested_origin)
        ctx = {
            "airline": {
                "name": airline.name,
                "title": airline.title,
            },
            "origin": {
                "name": self.requested_origin,  # Fixme: Add property name in Origin object
            },
            "schedule": await airline.get_schedule(self.requested_origin),
        }
        return self.json_response(ctx)
