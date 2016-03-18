"""
Adapter for the ebags.com items feed.
"""

import logging
import re
from typing import Sequence

from bs4 import BeautifulSoup

from aeroport.abc import UrlInfo, AbstractPayload
from aeroport.scraping import (
    AbstractUrlGenerator, AbstractItemAdapter, SchemeItem,
    BrowserScrapingOrigin, BrowserDownloader
)
from aeroport.destinations.stream import StreamDestination

from aeroport.airlines.like.payload import ShopItem, Brand


logger = logging.getLogger(__name__)

SHOP_TITLE = "eBags"
SHOP_NAME = "ebags"
SHOP_URL = "http://www.ebags.com"


class EbagsUrlGenerator(BrowserDownloader, AbstractUrlGenerator):

    FALLBACK_MAX_PAGE = 1
    ITEMS_ON_PAGE = 120
    USE_PROXY = True

    url_pattern = "%s/{category_url}#from{offset}" % SHOP_URL

    category_mapping = [
        {
            "category_name": "handbags",
            "category_url": "category/handbags/dept/handbags",
            "matching_category_id": 1,
        },
        {
            "category_name": "backpacks",
            "category_url": "search/dept/backpacks",
            "matching_category_id": 2,
        },
        {
            "category_name": "luggage",
            "category_url": "category/luggage/dept/luggage",
            "matching_category_id": 3,
        },
        {
            "category_name": "accessories",
            "category_url": "category/wallets/dept/accessories",
            "matching_category_id": 4,
        },
        {
            "category_name": "business",
            "category_url": "category/messenger-and-shoulder-bags/messenger-bags/dept/business",
            "matching_category_id": 6,
        },
        {
            "category_name": "business",
            "category_url": "category/business-cases/laptop-bags/dept/business",
            "matching_category_id": 7,
        },
        {
            "category_name": "sports",
            "category_url": "search/dept/sports",
            "matching_category_id": 8,
        },
    ]

    def __init__(self):
        super().__init__()
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

        url = self.get_category_page_url(self._processing_category, self._current_page)

        url_info = UrlInfo(url=url, kwargs=self._processing_category)

        return url_info

    def get_category_page_url(self, category, page_number) -> str:
        cat_copy = dict(category)
        cat_copy["offset"] = self.ITEMS_ON_PAGE * (page_number - 1)
        url = self.url_pattern.format(**cat_copy)
        return url

    async def get_max_page_number(self, category) -> int:

        url = self.get_category_page_url(category, page_number=1)
        html = await self.get_html_from_url(url)
        soup = BeautifulSoup(html, "html.parser")
        try:
            last_span = soup.find('span', {'data-bind': 'text:numPages'})
            max_page = int(last_span.text.strip())
        except (ValueError, AttributeError):
            logger.warning("Can not fetch max page number for category '%s'", category["category_name"])
            max_page = self.FALLBACK_MAX_PAGE

        return max_page


class BaseEbagsItemAdapter(AbstractItemAdapter):

    _shop_url = SHOP_URL
    _shop_title = SHOP_TITLE
    _shop_name = SHOP_NAME

    def _add_shop_info(self, payload: ShopItem) -> None:
        payload["shop_title"] = self._shop_title
        payload["shop_name"] = self._shop_name

    def extract_raw_items_from_html(self, html) -> Sequence:
        soup = BeautifulSoup(html, "html.parser")
        search_results_container = soup.find('div', {'id': 'srNew'})
        if search_results_container is None:
            logger.warning("No items found on a page")
            raw_items_list = tuple()
        else:
            raw_items_list = search_results_container.find_all('div', {'class': 'listPageItem'})
        return raw_items_list


class EbagsItemAdapter(BaseEbagsItemAdapter):

    def adapt_raw_item(self, raw_item) -> ShopItem:

        item_data = ShopItem()
        self._add_shop_info(item_data)

        try:

            # Extract image src
            image_container = raw_item.find('div', {'class': 'listPageImage'})
            image = image_container.find('img', {'class': 'responsiveListItem'})
            try:
                image_src = image["data-yo-src"]
                if image_src.startswith("data:image/"):
                    image_src = image["src"]
            except Exception:
                image_src = image["src"]
                if image_src.startswith("data:image/"):
                    image_src = image["data-yo-src"]

            if image_src[:2] == "//":
                image_src = "http://{}".format(image_src[2:])

            item_data["thumbnail_url"] = image_src

            item_info_container = raw_item.find('div', {'class': 'listPageItemInfo'})
            brand_container = item_info_container.find('div', {'class': 'itemBrandName'})
            link = brand_container.find('a')
            brand_name = link.text
            item_data["brand_title"] = brand_name

            href = link["href"]
            item_data["url"] = "{}{}".format(SHOP_URL, href)
            id_match = re.search("productid=(\d+)$", href)
            item_data["original_id"] = id_match.group(1)
            item_data["title"] = item_info_container.find('div', {'class': 'itemProductName'}).text

            price_str = item_info_container.find('div', {'class': 'itemProductPrice'}).text
            item_data["price"] = float(price_str.replace('$', ''))

            old_price_str = item_info_container.find('div', {'class': 'itemStrikeThroughPrice'}).text
            old_price_str = old_price_str.replace('$', '').strip()
            old_price = 0
            if old_price_str:
                old_price = float(old_price_str)
            item_data["oldprice"] = old_price


        except Exception as e:
            logger.warning(str(e))
            return None

        return item_data


class EbagsBrandAdapter(BaseEbagsItemAdapter):

    def adapt_raw_item(self, raw_item) -> Brand:

        item_data = Brand()

        try:
            brand_image_container = raw_item.find('div', {'class': 'listPageBrand'})
            brand_image = brand_image_container.find('img')
            brand_image_src = None
            if brand_image:
                brand_image_src = brand_image['src']
                if brand_image_src.startswith("data:image/"):
                    brand_image_src = brand_image['data-yo-src']

                if brand_image_src[:2] == "//":
                    brand_image_src = "http://{}".format(brand_image_src[2:])

            item_data["logo_url"] = brand_image_src

            item_info_container = raw_item.find('div', {'class': 'listPageItemInfo'})
            brand_container = item_info_container.find('div', {'class': 'itemBrandName'})
            link = brand_container.find('a')
            brand_name = link.text
            item_data["title"] = brand_name

        except Exception as e:
            logger.warning(str(e))
            return None

        return item_data


class Origin(BrowserScrapingOrigin):

    USE_PROXY = True

    SCRAPE_SCHEMES = (
        SchemeItem(
            urlgenerator=EbagsUrlGenerator,
            adapters=(
                (EbagsItemAdapter, {}),
                (EbagsBrandAdapter, {}),
            )
        ),
    )

    _shop_title = SHOP_TITLE
    _shop_name = SHOP_NAME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def default_destination(self):
        return StreamDestination()

    @property
    def name(self) -> str:
        return "ebags"
