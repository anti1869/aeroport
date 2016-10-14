"""
Things to extract data from Yandex Market Format (yml). Not to be confused with YAML.
"""

from enum import Enum
from typing import Optional, Dict, Iterable

from aeroport.abc import (
    AbstractOrigin, AbstractDownloader, AbstractUrlGenerator, AbstractItemAdapter, AbstractPayload,
)
from aeroport.payload import Payload, Field
from aeroport.dispatch import Flight


class YmlFeedItemTypes(Enum):
    category = 0
    offer = 1


class CategoryAdapter(AbstractItemAdapter):
    pass


class OfferAdapter(AbstractItemAdapter):
    pass


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

    @property
    def export_url(self):
        raise NotImplementedError()

    async def process(self):
        flight = Flight(self.airline, self)
        flight.start()

        # Preparations
        feed_file = self.get_feed_file(self.export_url)
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

    def get_feed_file(self, export_url: str) -> str:
        """
        Download feed or use local cache.

        :return: Full path on filesystem to prepared feed file.
        """
        return ""

    def analyze_feed(self, feed_file: str) -> FeedInfo:
        """
        Quickly get stats about feed.
        """
        info = FeedInfo()
        return info

    def parse_feed(self, feed_file: str, feed_info: Optional[FeedInfo]) -> Iterable[Dict]:
        return []
