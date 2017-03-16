"""
PostgreSQL database connector and some generic stuff.
"""

from collections import OrderedDict, namedtuple
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


FieldInfo = namedtuple('FieldResult', [
    'pk',  # Model field instance
    'fields',  # Dict of field name -> model field instance
    'forward_relations',  # Dict of field name -> RelationInfo
    'reverse_relations',  # Dict of field name -> RelationInfo
    'fields_and_pk',  # Shortcut for 'pk' + 'fields'
    'relations'  # Shortcut for 'forward_relations' + 'reverse_relations'
])


RelationInfo = namedtuple('RelationInfo', [
    'model_field',
    'related_model',
    'to_many',
    'to_field',
    'has_through_model'
])


class BaseModel(Model):
    """
    Base Peewee model for all other
    """

    db_manager = objects


    @classmethod
    def get_fields(cls) -> OrderedDict:
        fields = OrderedDict()
        fieldsgen = filter(lambda x: not (getattr(x[1], "rel_model", None)), cls._meta.fields.items())
        for name, field in fieldsgen:
            fields[name] = field
        return fields

    @classmethod
    def get_relations(cls) -> OrderedDict:
        return cls._get_forward_relationships(cls._meta)

    @classmethod
    def _get_to_field(cls, field):
        # return getattr(field, 'to_fields', None) and field.to_fields[0]
        return getattr(field, 'to_field', None)

    @classmethod
    def _get_forward_relationships(cls, opts):
        """
        Returns an `OrderedDict` of field names to `RelationInfo`.
        """
        forward_relations = OrderedDict()
        fieldsgen = filter(lambda x: bool(getattr(x[1], "rel_model", None)), opts.fields.items())
        for name, field in fieldsgen:
            forward_relations[name] = RelationInfo(
                model_field=field,
                related_model=field.rel_model,
                to_many=False,
                to_field=cls._get_to_field(field),
                has_through_model=False
            )
        #
        # Deal with forward many-to-many relationships.
        for field in getattr(opts, "many_to_many", tuple()):
            forward_relations[field.name] = RelationInfo(
                model_field=field,
                related_model=field.rel_model,
                to_many=True,
                # manytomany do not have to_fields
                to_field=None,
                has_through_model=False,  # TODO: Fix this in ManyToMany field implementation
                # has_through_model=(
                #     not field.rel_model.get_through_model()._meta.auto_created
                # )
            )

        return forward_relations

    @classmethod
    def _get_reverse_relationships(cls, opts):
        """
        Returns an `OrderedDict` of field names to `RelationInfo`.
        """
        return {}

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
