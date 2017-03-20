"""
Destination registration view
"""

from aiohttp import web_exceptions
import simplejson as json

from sunhead.conf import settings
from sunhead.rest.views import JSONView

from aeroport.destinations.models import Destination


class BaseDestinationView(JSONView):

    @property
    def requested_destination(self):
        id_ = self.request.match_info.get("destination", None)
        return int(id_) if id_ else None

    def json_response(self, context_data=None, status=None):
        context_data.update(
            {
                "requested_destination": self.requested_destination,
            }
        )
        return super().json_response(context_data)

    def _extract_fields(self, item):
        fields = item._meta.model_class.get_fields()
        data = {
            name: getattr(item, name, None)
            for name in fields.keys()
        }
        return data

    def _get_json_field(self, txt):
        if txt is not None:
            return json.loads(txt)


class DestinationsListView(BaseDestinationView):

    async def get(self):
        destinations = await Destination.db_manager.execute(
            Destination.select()
        )
        ctx = {
            "destinations": [
                self._extract_fields(item) for item in destinations
            ]
        }
        return self.json_response(ctx)

    async def post(self):
        data = await self.request.post()
        kwargs = {
            "settings": self._get_json_field(data.get("settings", None)),
            "class_name": data.get("class_name"),
            "name": data.get("name"),
            "enabled": str(data.get("enabled")).lower() in {"true", "1"},
        }
        destination = await Destination.db_manager.create(Destination, **kwargs)
        kwargs["id"] = destination.id
        url = "{}/{}".format(settings.REST_URL_PREFIX, "destinations/{}/".format(destination.id))
        return self.created_response(kwargs, url)


class DestinationView(BaseDestinationView):

    async def get(self):
        destination = await self._get_destination()
        ctx = {
            "destination": self._extract_fields(destination),
        }
        return self.json_response(ctx)

    async def put(self):
        destination = await self._get_destination()
        data = await self.request.post()
        destination.settings = self._get_json_field(data.get("settings", None))
        destination.class_name = data.get("class_name")
        destination.name = data.get("name")
        destination.enabled = str(data.get("enabled")).lower() in {"true", "1"}
        await Destination.db_manager.update(destination)

        raise web_exceptions.HTTPNoContent

    async def delete(self):
        destination = await self._get_destination()
        await Destination.db_manager.delete(destination)
        raise web_exceptions.HTTPNoContent

    async def _get_destination(self) -> Destination:
        destination = await Destination.db_manager.get(
            Destination, id=self.requested_destination
        )
        return destination
