"""
Adapter for the zappos.com items feed
"""

import re
import logging

from bs4 import BeautifulSoup

from aeroport.abc import UrlInfo
from aeroport.scraping import (
    AbstractUrlGenerator, AiohttpDownloader, AbstractItemAdapter, SchemeItem,
    AiohttpScrapingOrigin, BrowserScrapingOrigin,
)
from aeroport.destinations.console import ConsoleDestination
from aeroport.airlines.like.payload import ShopItem


logger = logging.getLogger(__name__)

SHOP_TITLE = "Zappos"
SHOP_NAME = "zappos"
SHOP_URL = "http://zappos.com"


class ZapposUrlGenerator(AiohttpDownloader, AbstractUrlGenerator):

    FALLBACK_MAX_PAGE = 1

    url_pattern = "%s/{category_name}{code1}#!/" \
                  "{category_name_page}-page{page_number}/{code2}.zso?p={page_number_zero}" % SHOP_URL

    category_mapping = (
        {
            "category_name": "handbags",
            "category_name_page": "handbags",
            "code1": "%7E5j",
            "code2": "COjWARCS1wHiAgIBAg",
            "primary_local_category_id": 1,
        },
        {
            "category_name": "backpacks",
            "category_name_page": "backpacks",
            "code1": "~1N",
            "code2": "COjWARCQ1wHiAgIBAg",
            "primary_local_category_id": 2,
        },
        {
            "category_name": "luggage-bags",
            "category_name_page": "luggage",
            "code1": "~5",
            "code2": "COjWARCT1wHiAgIBAg",
            "primary_local_category_id": 3,
        },
        {
            "category_name": "wallets-accessories",
            "category_name_page": "wallets-accessories",
            "code1": "%7Ew",
            "code2": "COjWARCW1wHiAgIBAg",
            "primary_local_category_id": 4,
        },
        {
            "category_name": "duffle-bags",
            "category_name_page": "duffle-bags",
            "code1": "~3",
            "code2": "COjWARCj1wHiAgIBAg",
            "primary_local_category_id": 5,
        },
        {
            "category_name": "messenger-bags",
            "category_name_page": "messenger-bags",
            "code1": "~L",
            "code2": "COjWARCU1wHiAgIBAg",
            "primary_local_category_id": 6,
        },
        {
            "category_name": "laptop-bags",
            "category_name_page": "laptop-bags",
            "code1": "~12",
            "code2": "COjWARCY1wHiAgIBAg",
            "primary_local_category_id": 7,
        },
        {
            "category_name": "bags-packs-sporting-goods",
            "category_name_page": "bags-packs",
            "code1": "~3",
            "code2": "CLDXARDJ2QHiAgIBAg",
            "primary_local_category_id": 8,
        },
    )

    def __init__(self):
        self._max_page = 0
        self._current_page = 0
        self._categories_gen = (c for c in self.category_mapping)
        self._processing_category = None

    async def __anext__(self) -> UrlInfo:
        if not self._processing_category or self._current_page >= self._max_page:
            self._processing_category = next(self._categories_gen, None)
            if self._processing_category is None:
                raise StopAsyncIteration
            self._max_page = await self.get_max_page_number(self._processing_category)
            self._current_page = 1
        else:
            # Remove comment for debug
            raise StopAsyncIteration
            self._current_page += 1

        url = self.url_pattern.format(
            page_number=self._current_page,
            page_number_zero=self._current_page - 1,
            **self._processing_category)

        url_info = UrlInfo(url=url, kwargs=self._processing_category)

        return url_info

    async def get_max_page_number(self, category):
        url = self.url_pattern.format(page_number=1, page_number_zero=0, **category)
        html = await self.get_html_from_url(url)
        soup = BeautifulSoup(html, "html.parser")
        try:
            last_span = soup.find('span', {'class': 'last'})
            a_tag = last_span.find('a', {'class': 'pager'})
            max_page = int(a_tag.text)
        except (ValueError, AttributeError):
            logger.warning("Can not fetch max page number for category '%s'", category["category_name"])
            return self.FALLBACK_MAX_PAGE

        return max_page


class ZapposItemAdapter(AbstractItemAdapter):

    def extract_raw_items_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        search_results_container = soup.find('div', {'id': 'searchResults'})
        raw_items_list = search_results_container.find_all('a', {'class': 'product'})
        return raw_items_list

    def adapt_raw_item(self, raw_item) -> ShopItem:
        """
        Convert data from the raw html object data into Payload object.

        :param raw_item: raw html object, representing item with the some interface.
        :return: Adapted and fully function ItemData instance
        :rtype: ItemData
        """

        item_data = ShopItem()

        #
        # # Assign local category id if possible
        # if "category" in kwargs:
        #     item_data.primary_local_category_id = kwargs["category"]["primary_local_category_id"]

        # Assign other fields
        try:
            item_data["url"] = SHOP_URL + raw_item["href"]
            item_data["original_id"] = "{}{}".format(
                raw_item["data-product-id"], raw_item["data-style-id"]
            )
            item_data["thumbnail_uri"] = raw_item.find('img', {'class': 'productImg'})['src']
            item_data["brand_title"] = raw_item.find('span', {'class': 'brandName'}).text
            item_data["title"] = raw_item.find('span', {'class': 'productName'}).text
            price_str = raw_item.find('span', {'class': 'price'}).text
            item_data["price"] = float(price_str.replace('$', ''))
        except (KeyError, AttributeError, ValueError):
            return None

        try:
            discount_str = raw_item.find('span', {'class': 'discount'}).text
            discount_match = re.search('\$([0-9\.]+)\)', discount_str)
            old_price = float(discount_match.group(1))
        except (ValueError, AttributeError):
            old_price = 0.0

        item_data["oldprice"] = old_price
        item_data["discount"] = round(100 - round(100 * item_data["price"] / item_data["oldprice"])) \
            if item_data["oldprice"] else 0

        return item_data


class Origin(AiohttpScrapingOrigin):

    SCRAPE_SCHEMES = (
        SchemeItem(
            urlgenerator=ZapposUrlGenerator,
            adapters=(
                (ZapposItemAdapter, {}),
            )
        ),
    )

    @property
    def default_destination(self):
        return ConsoleDestination()

    def postprocess_payload(self, payload: ShopItem, **kwargs) -> None:
        payload["primary_local_category_id"] = kwargs.get("primary_local_category_id", None)
        payload["category_name"] = kwargs.get("category_name", None)
        payload["shop_title"] = SHOP_TITLE
        payload["shop_name"] = SHOP_NAME
