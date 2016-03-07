"""
This destination just print payload to stdout
"""

from pprint import pprint

from aeroport.abc import AbstractDestination, AbstractPayload


class ConsoleDestination(AbstractDestination):

    async def process_payload(self, payload: AbstractPayload):
        pprint(payload.as_dict)
