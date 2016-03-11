"""
Defining and working with payload.
"""

from aeroport.abc import AbstractPayload, AbstractField


class Field(AbstractField):
    """Container of field metadata"""


class Payload(AbstractPayload):

    def postprocess(self, **kwargs):
        pass

