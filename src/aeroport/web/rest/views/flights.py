"""
Processing jobs views
"""

import logging

from aiohttp import web_exceptions

from sunhead.rest.views import JSONView
from sunhead.serializers.json import JSONSerializer

from aeroport.dispatch import FlightRecord, process_origin, ProcessingException


logger = logging.getLogger(__name__)
serializer = JSONSerializer()


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
        options = serializer.deserialize(data.get("options", "{}"))
        if not all((airline_name, origin_name)):
            raise web_exceptions.HTTPBadRequest

        try:
            await process_origin(
                airline_name, origin_name, destination_name,
                use_await=False, **options
            )
        except ProcessingException:
            raise web_exceptions.HTTPExpectationFailed

        raise web_exceptions.HTTPNoContent
