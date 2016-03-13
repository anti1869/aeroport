"""
Send payload to the Stream (messaging abstraction, provided by SunHead framework.
"""

import asyncio
from sunhead.events.stream import init_stream_from_settings

from aeroport.abc import AbstractDestination, AbstractPayload

# FIXME: Temporary setting here
from aeroport.airlines.like.common import STREAM_CONFIG


loop = asyncio.get_event_loop()
stream = loop.run_until_complete(init_stream_from_settings(STREAM_CONFIG))
loop.run_until_complete(stream.connect())


class StreamDestination(AbstractDestination):

    async def process_payload(self, payload: AbstractPayload):
        await stream.publish(payload.as_dict, ("aeroport.payload_sent", ))
