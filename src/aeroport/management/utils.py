"""
Managing airlines, their origins, destinations and other stuff.
"""

from typing import Tuple

from sunhead.conf import settings
from sunhead.utils import get_submodule_list, get_class_by_path

from aeroport.abc import AirlineDescription, AbstractAirline


__all__ = (
    "get_airlines_list", "get_airline",
)


def get_airlines_list() -> Tuple[AirlineDescription]:
    subs = (
        AirlineDescription(name=sub.name, module_path=sub.path)
        for sub in get_submodule_list(settings.AIRLINES_MOUNT_POINT)
    )
    result = tuple(subs)
    return result


def get_airline(name: str) -> AbstractAirline:
    airline_classname = settings.AIRLINE_CLASS_PATH_TEMPLATE.format(name=name)
    kls = get_class_by_path(airline_classname)
    airline = kls()
    return airline
