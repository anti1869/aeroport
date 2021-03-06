"""
Abstracts and bases for building adapters, item definitions, etc...

Payload abstractions taken from Scrapy projects.
"""

from abc import ABCMeta, abstractmethod
from collections import namedtuple, MutableMapping, AsyncIterable
from typing import Tuple, Sequence, Optional, Dict

from sunhead.conf import settings
from sunhead.utils import get_submodule_list, get_class_by_path

from aeroport.db import objects
from aeroport.management.models import AirlineSettings, OriginSettings

AirlineDescription = namedtuple("AirlineDescription", "name module_path")
OriginDescription = namedtuple("OriginDescription", "name module_path")
UrlInfo = namedtuple("UrlInfo", "url kwargs")


class AbstractField(dict):
    pass


class InheritableFieldsMeta(ABCMeta):
    # This was ItemMeta from Scrapy

    def __new__(mcs, class_name, bases, attrs):
        # Collect fields from base classes and put to this one
        new_bases = tuple(base._class for base in bases if hasattr(base, '_class'))
        _class = super().__new__(mcs, 'x_' + class_name, new_bases, attrs)

        fields = getattr(_class, 'fields', {})
        new_attrs = {}
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, AbstractField):
                fields[n] = v
            elif n in attrs:
                new_attrs[n] = attrs[n]

        new_attrs['fields'] = fields
        new_attrs['_class'] = _class
        return super().__new__(mcs, class_name, bases, new_attrs)


class DictItem(MutableMapping):
    # This was DictItem from Scrapy

    fields = {}

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args or kwargs:  # avoid creating dict for most common case
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value
        else:
            raise KeyError("%s does not support field: %s" %
                (self.__class__.__name__, key))

    def __delitem__(self, key):
        del self._values[key]

    def __getattr__(self, name):
        if name in self.fields:
            raise AttributeError("Use item[%r] to get field value" % name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            raise AttributeError("Use item[%r] = %r to set field value" %
                (name, value))
        super().__setattr__(name, value)

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def keys(self):
        return self._values.keys()

    def copy(self):
        return self.__class__(self)


class AbstractPayload(DictItem, metaclass=InheritableFieldsMeta):

    @property
    def as_dict(self):
        return self._values


class AbstractDestination(object, metaclass=ABCMeta):

    def __init__(self, **init_kwargs):
        self._init_kwargs = init_kwargs

    @abstractmethod
    async def prepare(self):
        pass

    @abstractmethod
    async def release(self):
        pass

    @abstractmethod
    async def process_payload(self, payload: AbstractPayload) -> None:
        pass


class AbstractOrigin(object, metaclass=ABCMeta):

    def __init__(self, airline):
        self._destination = None
        self._airline = airline
        self._settings = None

    async def set_destination(self, class_path: str, **init_kwargs):
        kls = get_class_by_path(class_path)
        self._destination = kls(**init_kwargs)
        await self._destination.prepare()

    def set_options(self, **options):
        """
        Set configuration options for the origin, that will affect its processing.
        """

    @property
    def airline(self):
        return self._airline

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def process(self) -> None:
        pass

    @property
    @abstractmethod
    def default_destination(self):
        pass

    @property
    def destination(self):
        if self._destination is None:
            self._destination = self.default_destination
        return self._destination

    async def send_to_destination(self, payload: AbstractPayload):
        if self.destination is None:
            raise ValueError("You must set destination first")
        await self.destination.process_payload(payload)

    @property
    async def settings(self) -> Dict:
        if self._settings is None:
            self._settings = await OriginSettings.get_settings(self)
        return self._settings


class AbstractAirline(object, metaclass=ABCMeta):
    """
    Common interface for all airlines. Airline package must provide this object in its registration module.
    E.g. ``aeroport.airlines.air_example.registration.Airline``.

    So that airline autodiscover will work.
    """

    def __init__(self):
        self._settings = None

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
        origin_class_path = "{}.{}.Origin".format(self.origins_mount_point, origin_name)
        kls = get_class_by_path(origin_class_path)
        origin = kls(airline=self)
        return origin

    async def _get_settings_obj(self):
        obj, _ = await objects.get_or_create(AirlineSettings, airline=self.name)
        return obj

    async def is_enabled(self) -> bool:
        settings_obj = await self._get_settings_obj()
        result = settings_obj.enabled
        return result

    async def set_is_enabled(self, value: bool) -> None:
        settings_obj = await self._get_settings_obj()
        settings_obj.enabled = value
        await objects.update(settings_obj, only=("enabled", ))

    async def get_schedule(self, origin: Optional[str] = None) -> Dict:
        settings_obj = await self._get_settings_obj()
        schedule = settings_obj.schedule if settings_obj.schedule is not None else {}

        if origin is not None:
            schedule = {
                origin: schedule.get(origin, {})
            }

        return schedule

    async def set_schedule(self, schedule_data: Dict) -> None:
        settings_obj = await self._get_settings_obj()
        settings_obj.schedule = schedule_data
        await objects.update(settings_obj, only=("schedule",))


class AbstractUrlGenerator(AsyncIterable):
    async def __aiter__(self):
        return self

    @abstractmethod
    async def __anext__(self) -> UrlInfo:
        pass


class AbstractItemAdapter(object, metaclass=ABCMeta):

    def gen_payload_from_html(self, html):
        raw_items = self.extract_raw_items_from_html(html)
        return map(self.adapt_raw_item, raw_items)

    @abstractmethod
    def extract_raw_items_from_html(self, html) -> Sequence:
        return []

    @abstractmethod
    def adapt_raw_item(self, raw_item) -> AbstractPayload:
        return None


class AbstractDownloader(object, metaclass=ABCMeta):
    @abstractmethod
    async def get_html_from_url(self, url: str) -> str:
        pass
