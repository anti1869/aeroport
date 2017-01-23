"""
Things to extract data from Yandex Market Format (yml). Not to be confused with YAML.
"""

from copy import copy
from enum import Enum
from functools import partial
import hashlib
import logging
import os
import time
from typing import Optional, Dict, Iterable, Sequence, Generator
from xml.etree import cElementTree as ET
from xml.etree.cElementTree import iterparse


from sunhead.conf import settings
from sunhead.utils import get_class_by_path

from aeroport.abc import (
    AbstractOrigin, AbstractDownloader, AbstractUrlGenerator, AbstractItemAdapter, AbstractPayload,
)
from aeroport.payload import Payload, Field
from aeroport.dispatch import Flight
from aeroport.fileurlcache import FileUrlCache


logger = logging.getLogger(__name__)


class YmlFeedItemTypes(Enum):
    category = 0
    offer = 1


class XMLElementsCollection(object):

    def __init__(self, first_element=None):
        self._data = []
        if first_element is not None:
            self._data.append(copy(first_element))

    def accept_element(self, element):
        # TODO: Check memory consumption in this case
        self._data.append(copy(element))

    def get_raw_item(self) -> Sequence[ET.Element]:
        return self._data


def get_attrib(elem, names, cast_type=None, default=None):
    """
    Get attribute of xml element tag which name can be on the provided list.
    First found returned.

    :param elem: XML element to search attributes in.
    :param names: List of possible attribute names.
    :param default: Return value if not one single name found in elem.attribs.
    :return: Value of the attribute as a string.
    :rtype: str
    """
    for name in names:
        if name in elem.attrib:
            result = elem.attrib[name]
            if cast_type:
                try:
                    result = cast_type(result)
                except ValueError as e:
                    # There is problem casting type. Try to workaround
                    if cast_type == int:
                        int(hashlib.md5(result).hexdigest()[:16], 16)
                    else:
                        raise ValueError(e)
            return result
    return default


class YMLItemAdapter(AbstractItemAdapter):
    """
    Concrete airline must subclass and implement this adapter.
    """
    def extract_raw_items_from_html(self, html) -> Sequence:
        raise NotImplementedError()


class FeedInfo(Payload):
    """
    Information about feed that can be interest to someone.
    """
    shop_name = Field()
    total_count = Field()
    categories_count = Field()
    offers_count = Field()
    filesize = Field()
    file_last_updated = Field()
    file_last_updated_formatted = Field()


class FeedParsingResult(Payload):
    """
    After parsing the whole feed, this should be sent to the destination, so that
    remote subscribers can do their cleanup such as delete non-existing items in feed.
    """
    shop_name = Field()
    offers_id_list = Field()
    categories_id_list = Field()


class YmlOrigin(AbstractOrigin):
    """
    This origin will download remote YML feeds to local temporary storage (if there is no
    fresh file there already) and process its items and categories. Object will be fed
    to the item and categories adapters (which must be implemented separately from this class)
    and the result will be sent to the destination.
    """

    ADAPTER_MAPPING = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._adapters = {
            item_type: kls() for item_type, kls in self.ADAPTER_MAPPING.items()
        }
        self._cache = self._init_file_url_cache()

    def _init_file_url_cache(self) -> FileUrlCache:
        conf = dict(settings.FILE_URL_CACHE["storage"])
        bucket = "{}_{}".format(conf.pop("bucket"), self.airline.name)
        storage_class = get_class_by_path(conf.pop("class"))
        expires = settings.FILE_URL_CACHE.get("expires", None)
        storage = storage_class(**conf)
        cache = FileUrlCache(storage, bucket, expires)
        return cache

    @property
    def export_url(self):
        raise NotImplementedError()

    async def get_urlgenerator(self) -> AbstractUrlGenerator:
        raise NotImplementedError()

    async def progress_callback(self, processed: int, total: int):
        pc = int(processed * 100 / total)
        logger.info("%s %% Processed %s of %s yml items", pc, processed, total)

    async def process(self):
        """
        Starting point for feeds consuming. Several feeds will be processed, as yielded
        by urlgenerator.
        """

        flight = Flight(self)
        await flight.start()

        total_processed = 0
        async for url_info in await self.get_urlgenerator():
            procesed = await self.process_export_url(url_info.url, url_info.kwargs)
            total_processed += procesed
            await flight.set_num_processed(total_processed)

        await flight.finish(total_processed)

    async def process_export_url(self, export_url: str, url_kwargs: Dict) -> Optional[int]:
        """
        Process one given feed url.

        :return: Processed number
        """

        # Preparations
        shop_name = url_kwargs.get("shop_name")
        if shop_name is None:
            return

        feed_file = await self.get_feed_file(export_url, shop_name)
        if feed_file is None:
            logger.error("Can't get valid feed file, aborting")
            return

        feed_info = self.analyze_feed(feed_file, shop_name)
        await self.send_to_destination(feed_info)

        # Parsing process
        idx = 0
        id_lists = {
            YmlFeedItemTypes.category: set(),
            YmlFeedItemTypes.offer: set(),
        }
        for idx, item in enumerate(filter(None, self.parse_feed(feed_file)), start=1):
            if idx % 100 == 0:
                await self.progress_callback(idx, feed_info["total_count"])

            adapter = self._adapters.get(item["type"], None)
            if not adapter:
                continue
            id_lists.get(item["type"], set()).add(item["original_id"])
            item["payload"].postprocess(
                **{
                    "origin_name": self.name,
                    "url_kwargs": url_kwargs,
                }
            )
            await self.send_to_destination(item["payload"])

        # Finalize
        result = FeedParsingResult(
            shop_name=shop_name,
            categories_id_list=id_lists[YmlFeedItemTypes.category],
            offers_id_list=id_lists[YmlFeedItemTypes.offer]
        )
        await self.send_to_destination(result)

        return idx

    async def get_feed_file(self, export_url: str, shop_name: str, force_download=False) -> str:
        """
        Download feed or use local cache.

        :return: Full path on filesystem to prepared feed file.
        """
        as_filename = "{}.yml".format(shop_name)
        path = await self._cache.get(export_url, as_filename, force_download)
        return path

    def analyze_feed(self, feed_file: str, shop_name: Optional[str] = None) -> Optional[FeedInfo]:
        """
        Quickly get stats about feed.
        """
        logger.info("Analyzing feed")
        info = FeedInfo()
        if not os.path.isfile(feed_file):
            return None
        info["file_last_updated"] = os.path.getmtime(feed_file)
        info["file_last_updated_formatted"] = time.strftime(
            "%d.%m.%Y %H:%M", time.localtime(info["file_last_updated"])
        )
        info["filesize"] = float(os.path.getsize(feed_file)) / 1024.0 / 1024.0
        categories_count, offers_count = 0, 0
        with open(feed_file, "r") as f:
            for line in f:
                categories_count += line.count("<category ")
                offers_count += line.count("<offer ")

        info["categories_count"] = categories_count
        info["offers_count"] = offers_count
        info["total_count"] = categories_count + offers_count
        info["shop_name"] = shop_name
        return info

    def parse_feed(self, feed_file: str) -> Iterable[Dict]:
        yield from self._parse(
            feed_file,
            categories_parser=partial(self._generator, "category", "categories"),
            offers_parser=partial(self._generator, "offer", "offers")
        )

    def _parse(self, feed_file: str, categories_parser=None, offers_parser=None):
        """
        This will run process of iteration through all elements in a Feed, applying parsing method
        to categories and items collections.

        :param feed_file: Path to the feed file.
        :param categories_parser: Method that will parse all categories in given context.
        :param offers_parser: Method that will parse all items in given context.
        :return: Doesn"t return anything.
        """
        # Check what caller was intended to parse and put memory cleaning iterators to unneeded
        # portions of YML XML
        if categories_parser is None:
            categories_parser = partial(self._dismiss_generator, "categories")
        if offers_parser is None:
            offers_parser = partial(self._dismiss_generator, "offers")

        # Start XML parsing process right from the beginning, using configured parsers
        context = iter(iterparse(feed_file, events=("start", "end")))
        for event, elem in context:
            if event == "start":
                if elem.tag == "categories":
                    logging.info("Parser enters categories")
                    for i in categories_parser(context):
                        yield i
                if elem.tag == "offers":
                    logging.info("Parser enters offers")
                    for i in offers_parser(context):
                        yield i
            else:
                if elem.tag == "offers" or elem.tag == "categories":
                    elem.clear()

    def _dismiss_generator(self, stop_on, context):
        for event, elem in context:
            if event == "end":
                elem.clear()
                if elem.tag == stop_on:
                    yield None
                    raise StopIteration()

    def _generator(self, key, tag_many, context):
        for event, elem in context:
            if event == "start" and elem.tag == key:
                raw_data_collector = XMLElementsCollection(elem)
                for key_event, key_elem in context:
                    if key_event == "end":
                        if key_elem.tag == key:
                            key_elem.clear()
                            payload = self._adapters[getattr(YmlFeedItemTypes, key)].adapt_raw_item(
                                raw_data_collector.get_raw_item()
                            )
                            yield {
                                "type": getattr(YmlFeedItemTypes, key),
                                "original_id": payload.get("original_id", None),
                                "payload": payload,
                            }
                            break
                        else:
                            raw_data_collector.accept_element(key_elem)
            elif event == "end" and elem.tag == tag_many:
                elem.clear()
                raise StopIteration()
