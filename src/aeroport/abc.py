"""
Abstracts and bases for building adapters, item definitions, etc...
"""

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import Tuple

from sunhead.conf import settings
from sunhead.utils import get_submodule_list

AirlineDescription = namedtuple("AirlineDescription", "name module_path")
OriginDescription = namedtuple("OriginDescription", "name module_path")


class AbstractAirline(object, metaclass=ABCMeta):
    """
    Common interface for all airlines. Airline package must provide this object in its resigration module.
    E.g. ``aeroport.airlines.air_example.registration.Airline``.

    So that airline autodiscover will work.
    """

    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    def package_path(self) -> str:
        result = "{}.{}".format(settings.AIRLINES_MOUNT_POINT, self.name)
        return result

    @property
    def origins_mount_point(self) -> str:
        result = "{}.origins".format(self.package_path)
        return result

    def get_origin_list(self) -> Tuple[OriginDescription]:
        origins = (
            OriginDescription(name=sub.name, module_path=sub.path)
            for sub in get_submodule_list(self.origins_mount_point)
        )
        result = tuple(origins)
        return result

    def get_origin(self, origin_name) -> AbstractOrigin:
        pass


class AbstractOrigin(object, metaclass=ABCMeta):

    @abstractmethod
    def process(self) -> None:
        pass
