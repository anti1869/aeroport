"""
PostgreSQL database connector and some generic stuff.
"""

from itertools import chain
from enum import Enum
import logging
from typing import Optional, Iterable, List, Tuple

import peewee
from peewee import Model, BaseModel as PeeweeBaseModel
from peewee_async import Manager


from sunhead.conf import settings
from sunhead.utils import get_class_by_path

logger = logging.getLogger(__name__)


master_settings = dict(settings.DATABASE[settings.DATABASE_PRESET])

engine_kls = get_class_by_path(master_settings.pop('engine'))
db = engine_kls(**master_settings)


objects = Manager(db)


class BaseModel(Model):
    """
    Base Peewee model for all other
    """

    db_manager = objects

    class Meta:
        database = db


def get_models_from_module(module, base) -> Iterable[PeeweeBaseModel]:
    """
    Get models from provided module which have ``base`` class.

    :param module: Module from which to extract models.
    :param base: Base class to look for.
    :return: Sequence of models
    """
    all_models = filter(
        lambda x: isinstance(x, PeeweeBaseModel) and base in x.__bases__,
        module.__dict__.values()
    )
    return all_models


def get_all_models() -> List[Model]:
    # TODO: Implement that properly
    from aeroport.management import models as management_models
    from aeroport.destinations import models as destination_models
    from aeroport import dispatch
    all_models = list(chain(
        get_models_from_module(management_models, BaseModel),
        get_models_from_module(destination_models, BaseModel),
        get_models_from_module(dispatch, BaseModel),
    ))
    return all_models


def create_tables(models: Optional[Iterable[Model]] = None) -> None:
    """Only create the tables if they do not exist."""
    if models is None:
        models = get_all_models()
    db.create_tables(models, safe=True)
    # for model in models:
    #     m2ms = getattr(model._meta, "many_to_many", None)
    #     through_models = [m2m.get_through_model() for m2m in m2ms]
    #     db.create_tables(through_models, safe=True)


def drop_tables(models: Optional[Iterable[str]] = None) -> None:
    """Drops all existing tables"""
    if models is None:
        models = get_all_models()
    try:
        db.drop_tables(models, safe=True, cascade=True)
        # for model in models:
        #     m2ms = getattr(model._meta, "many_to_many", None)
        #     through_models = [m2m.get_through_model() for m2m in m2ms]
        #     db.drop_tables(through_models, safe=True)
    except peewee.ProgrammingError:
        logger.warning("Error while dropping tables", exc_info=True)


def choices_from_enum(source: Enum) -> Tuple[int, str]:
    """
    Makes tuple to use in Django's Fields ``choices`` attribute.
    Enum members names will be titles for the choices.

    :param source: Enum to process.
    :return: Tuple to put into ``choices``
    """
    result = tuple((s.value, s.name.title()) for s in source)
    return result
