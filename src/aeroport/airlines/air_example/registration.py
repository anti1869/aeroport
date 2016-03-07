"""
Conventional interface to Airline. Must actually provide Airline object with known interface.
"""

from aeroport.abc import AbstractAirline


class Airline(AbstractAirline):

    @property
    def name(self) -> str:
        return "air_example"

    @property
    def title(self) -> str:
        return "Air Example"
