import peewee
from playhouse.postgres_ext import BinaryJSONField

from aeroport.db import BaseModel


class Destination(BaseModel):
    """
    Persistent layer for destination settings.
    """
    class_name = peewee.CharField()
    name = peewee.CharField(index=True)
    enabled = peewee.BooleanField()
    settings = BinaryJSONField()

