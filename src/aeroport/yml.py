"""
Things to extract data from Yandex Market Format (yml). Not to be confused with YAML.
"""

from enum import Enum
import logging
from typing import Optional, Dict, Iterable, Sequence

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
        return None


class OfferAdapter(YMLItemAdapter):
    def adapt_raw_item(self, raw_item) -> AbstractPayload:
        return None


class FeedInfo(Payload):
    total_count = Field()
    categories_count = Field()
    offers_count = Field()
    filesize = Field()
    file_last_updated = Field()


class FeedParsingResult(Payload):
    offers_id_list = Field()
    categories_id_list = Field()


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

    async def process(self):
        feed_file = await self.get_feed_file(self.export_url)
        print(feed_file)
        feed_info = self.analyze_feed(feed_file)
        print(feed_info)

    async def process2(self):
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
        for idx, item in enumerate(self.parse_feed(feed_file, feed_info), start=1):
            adapter = self._adapters.get(item["type"], None)
            if not adapter:
                continue
            id_lists.get(item["type"], set()).add(item["original_id"])
            payload = adapter.adapt_raw_item(item)
            await self.send_to_destination(payload)

        # Finalize
        result = FeedParsingResult()
        result.categories_id_list = id_lists[YmlFeedItemTypes.category]
        result.offers_id_list = id_lists[YmlFeedItemTypes.offer]
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
        info = FeedInfo()
        return info

    def parse_feed(self, feed_file: str, feed_info: Optional[FeedInfo]) -> Iterable[Dict]:
        return []
