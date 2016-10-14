"""
Things to extract data from Yandex Market Format (yml). Not to be confused with YAML.
"""

from enum import Enum
from functools import partial
import logging
import os
import time
from typing import Optional, Dict, Iterable, Sequence
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


class YMLItemAdapter(AbstractItemAdapter):
    def extract_raw_items_from_html(self, html) -> Sequence:
        raise NotImplementedError()


class CategoryAdapter(YMLItemAdapter):
    def adapt_raw_item(self, raw_item) -> AbstractPayload:
        return Payload()


class OfferAdapter(YMLItemAdapter):
    def adapt_raw_item(self, raw_item) -> AbstractPayload:
        return Payload()


class FeedInfo(Payload):
    total_count = Field()
    categories_count = Field()
    offers_count = Field()
    filesize = Field()
    file_last_updated = Field()
    file_last_updated_formatted = Field()


class FeedParsingResult(Payload):
    offers_id_list = Field()
    categories_id_list = Field()


class XMLElementCollector(object):

    def __init__(self, element):
        self._data = []

    def accept_element(self, element):
        self._data.append(element)

    def get_raw_item(self):
        return self._data


class YmlOrigin(AbstractOrigin):

    ADAPTER_MAPPING = {
        YmlFeedItemTypes.category: CategoryAdapter,
        YmlFeedItemTypes.offer: OfferAdapter,
    }

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

    async def progress_callback(self, processed: int, total: int):
        pc = int(processed * 100 / total)
        logger.info("%s %% Processed %s of %s yml items", pc, processed, total)

    async def process(self):
        flight = Flight(self.airline, self)
        flight.start()

        # Preparations
        feed_file = await self.get_feed_file(self.export_url)
        if feed_file is None:
            logger.error("Can't get valid feed file, aborting")
            return

        feed_info = self.analyze_feed(feed_file)
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
            await self.send_to_destination(item["payload"])

        # Finalize
        result = FeedParsingResult(
            categories_id_list=id_lists[YmlFeedItemTypes.category],
            offers_id_list=id_lists[YmlFeedItemTypes.offer]
        )
        await self.send_to_destination(result)

        flight.finish(idx)

    async def get_feed_file(self, export_url: str, force_download=False) -> str:
        """
        Download feed or use local cache.

        :return: Full path on filesystem to prepared feed file.
        """
        as_filename = "{}.yml".format(self.name)
        path = await self._cache.get(export_url, as_filename, force_download)
        return path

    def analyze_feed(self, feed_file: str) -> FeedInfo:
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
                categories_count += line.count('<category ')
                offers_count += line.count('<offer ')

        info["categories_count"] = categories_count
        info["offers_count"] = offers_count
        info["total_count"] = categories_count + offers_count
        return info

    def parse_feed(self, feed_file: str) -> Iterable[Dict]:
        yield from self._parse(
            feed_file,
            categories_parser=self._categories_generator,
            # offers_parser=self._offers_generator
        )

    def _parse(self, feed_file: str, categories_parser=None, offers_parser=None):
        """
        This will run process of iteration through all elements in a Feed, applying parsing method to
        categories and items collections.

        :param feed_file: Path to the feed file.
        :param categories_parser: Method that will parse all categories in given context.
        :param offers_parser: Method that will parse all items in given context.
        :return: Doesn't return anything.
        """
        # Check what caller was intended to parse and put memory cleaning iterators to unneeded portions of YML XML
        if categories_parser is None:
            categories_parser = partial(self._dismiss_generator, 'categories')
        if offers_parser is None:
            offers_parser = partial(self._dismiss_generator, 'offers')

        # Start XML parsing process right from the beginning, using configured parsers
        context = iter(iterparse(feed_file, events=('start', 'end')))
        for event, elem in context:
            if event == 'start':
                if elem.tag == "categories":
                    for i in categories_parser(context):
                        yield i
                if elem.tag == "offers":
                    for i in offers_parser(context):
                        yield i
            else:
                if elem.tag == "offers" or elem.tag == "categories":
                    elem.clear()

    def _dismiss_generator(self, stop_on, context):
        for event, elem in context:
            if event == 'end':
                elem.clear()
                if elem.tag == stop_on:
                    yield None
                    raise StopIteration()

    # TODO: Squash next two
    def _offers_generator(self, context):
        for event, elem in context:
            if event == 'start' and elem.tag == "offer":
                raw_data_collector = XMLElementCollector(elem)
                for offer_event, offer_elem in context:
                    if offer_event == 'end':
                        if offer_elem.tag == 'offer':
                            offer_elem.clear()
                            offer_payload = self._adapters[YmlFeedItemTypes.offer].adapt_raw_item(
                                raw_data_collector.get_raw_item()
                            )
                            yield {
                                "type": YmlFeedItemTypes.offer,
                                "original_id": None,
                                "payload": offer_payload,
                            }
                        else:
                            raw_data_collector.accept_element(offer_elem)
            elif event == 'end' and elem.tag == 'offers':
                elem.clear()
                raise StopIteration()

    def _categories_generator(self, context):
        for event, elem in context:
            if event == 'start' and elem.tag == "category":
                raw_data_collector = XMLElementCollector(elem)
                for category_event, category_elem in context:
                    if category_event == 'end':
                        if category_elem.tag == 'offer':
                            category_elem.clear()
                            payload = self._adapters[YmlFeedItemTypes.category].adapt_raw_item(
                                raw_data_collector.get_raw_item()
                            )
                            yield {
                                "type": YmlFeedItemTypes.category,
                                "original_id": None,
                                "payload": payload,
                            }
                        else:
                            raw_data_collector.accept_element(category_elem)
            elif event == 'end' and elem.tag == 'categories':
                elem.clear()
                raise StopIteration()