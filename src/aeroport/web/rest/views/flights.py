"""
Processing jobs views
"""

import asyncio

from aiohttp import web_exceptions

from sunhead.rest.views import JSONView

from aeroport import management


class FlightsListView(JSONView):

    async def post(self):
        data = await self.request.post()
        airline_name = data.get("airline", None)
        origin_name = data.get("origin", None)
        if not all((airline_name, origin_name)):
            raise web_exceptions.HTTPBadRequest

        airline = management.get_airline(airline_name)
        origin = airline.get_origin(origin_name)
        asyncio.ensure_future(origin.process())

        raise web_exceptions.HTTPNoContent
