"""
Payload definitions. It is basically a schema for collected data.
"""

from aeroport.payload import Payload, Field


class Repo(Payload):
    title = Field()
    description = Field()
