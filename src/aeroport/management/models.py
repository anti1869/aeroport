import peewee
import peewee_async
from playhouse.postgres_ext import BinaryJSONField

from aeroport.db import BaseModel
from aeroport.destinations.models import Destination


class AirlineSettings(BaseModel):
    """
    Persistent layer for airline settings.
    """
    airline = peewee.CharField(index=True)
    enabled = peewee.BooleanField(default=True)
    schedule = BinaryJSONField(null=True)
    destinations = peewee.CharField(null=True)  # TODO: Switch to m2m

    async def get_destinations(self, only_enabled=True):
        if self.destinations is None:
            return tuple()

        names = str(self.destinations).split(",")
        q = Destination.select().where(Destination.name.in_(names))
        if only_enabled:
            q = q.where(Destination.enabled)
        destinations = await self.db_manager.execute(q)
        return destinations


class OriginSettings(BaseModel):
    """
    Persistent layer for origin settings.
    """
    airline = peewee.CharField()
    origin = peewee.CharField()
    settings = BinaryJSONField()

    @classmethod
    async def get_settings(cls, origin):
        try:
            obj = await cls.db_manager.get(
                cls,
                cls.airline == origin.airline.name,
                cls.origin == origin.name,
            )
            settings = obj.settings
        except cls.DoesNotExist:
            settings = {}

        return settings
