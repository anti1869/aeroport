"""
Processing jobs views
"""

import asyncio
import logging

from aiohttp import web_exceptions

from sunhead.rest.views import JSONView

from aeroport import management
from aeroport.destinations.models import Destination
from aeroport.dispatch import FlightRecord


logger = logging.getLogger(__name__)


class FlightsListView(JSONView):

    LIST_LIMIT = 50

    async def get(self):
        # TODO: Implement paging and other stuff
        latest = await FlightRecord.db_manager.execute(
            FlightRecord.select().limit(self.LIST_LIMIT).order_by(-FlightRecord.started)
        )
        data = [
            self._extract_fields(record) for record in latest
        ]
        return self.json_response(data)

    def _extract_fields(self, item):
        fields = item.__class__.get_fields()
        data = {
            name: getattr(item, name, None)
            for name in fields.keys()
        }
        return data

    async def post(self):
        data = await self.request.post()
        airline_name = data.get("airline", None)
        origin_name = data.get("origin", None)
        destination_name = data.get("destination", None)
        if not all((airline_name, origin_name)):
            raise web_exceptions.HTTPBadRequest

        airline = management.get_airline(airline_name)
        origin = airline.get_origin(origin_name)
        if destination_name:
            try:
                dest = await Destination.db_manager.get(Destination, enabled=True, name=destination_name)
            except Destination.DoesNotExist:
                logger.error("There is not destination named '%s'" % destination_name)
                raise web_exceptions.HTTPBadRequest
            else:
                await origin.set_destination(dest.class_name, **dest.settings)

        asyncio.ensure_future(origin.process())

        raise web_exceptions.HTTPNoContent
