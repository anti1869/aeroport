"""
Send payload to the Stream (messaging abstraction, provided by SunHead framework.
"""

import asyncio

from sunhead.events.stream import init_stream_from_settings
from sunhead.metrics import get_metrics

from aeroport.abc import AbstractDestination, AbstractPayload


class StreamDestination(AbstractDestination):
    """
    Send payloads to the SunHead framework's stream (which is distributed queues).
    """

    def __init__(self, **init_kwargs):
        super().__init__(**init_kwargs)
        self._stream = None
        self._loop = asyncio.get_event_loop()
        self._metrics = get_metrics()
        self._metric_sent = self._metrics.prefix("stream_payloads_sent_total")
        self._metrics.add_counter(self._metric_sent, "")

    async def prepare(self):
        self._stream = await init_stream_from_settings(self._init_kwargs)
        await self._stream.connect()

    async def release(self):
        await self._stream.close()

    async def process_payload(self, payload: AbstractPayload):
        pname = payload.__class__.__name__.lower()
        await self._stream.publish(payload.as_dict, ("aeroport.payload_sent.{}".format(pname), ))
        self._metrics.counters.get(self._metric_sent).inc()
