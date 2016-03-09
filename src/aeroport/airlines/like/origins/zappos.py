"""
Adapter for the zappos.com items feed
"""

import re
import logging
import asyncio
from functools import partial

from bs4 import BeautifulSoup

from aeroport.browserscraper import BrowserScraper
from aeroport.airlines.like.payload import ShopItem


logger = logging.getLogger(__name__)


class Origin(BrowserScraper):

    url_pattern = "http://www.zappos.com/{category_name}{code1}#!/" \
              "{category_name_page}-page{page_number}/{code2}.zso?p={page_number_zero}"

    category_mapping = [
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
    ]

    def extract_raw_items_from_html(self, url):

        soup = BeautifulSoup(html, "html.parser")
        search_results_container = soup.find('div', {'id': 'searchResults'})
        raw_items_list = search_results_container.find_all('a', {'class': 'product'})
        return raw_items_list

    def adapt_raw_item(self, raw_item, **kwargs) -> ItemData:
        """
        Convert data from the raw html object data into ItemData object.

        :param raw_item: raw html object, representing item with the some interface.
        :return: Adapted and fully function ItemData instance
        :rtype: ItemData
        """

        item_data = ItemData()

        # Assign local category id if possible
        if "category" in kwargs:
            item_data.primary_local_category_id = kwargs["category"]["primary_local_category_id"]

        # Assign other fields
        try:
            item_data.url = "http://zappos.com" + raw_item["href"]
            item_data.original_id = "{}{}".format(
                raw_item['data-product-id'], raw_item['data-style-id']
            )
            item_data.thumbnail_uri = raw_item.find('img', {'class': 'productImg'})['src']
            item_data.brand_title = raw_item.find('span', {'class': 'brandName'}).text
            item_data.title = raw_item.find('span', {'class': 'productName'}).text
            price_str = raw_item.find('span', {'class': 'price'}).text
            item_data.price = float(price_str.replace('$', ''))
        except (KeyError, AttributeError, ValueError):
            return None

        try:
            discount_str = raw_item.find('span', {'class': 'discount'}).text
            discount_match = re.search('\$([0-9\.]+)\)', discount_str)
            old_price = float(discount_match.group(1))
        except (ValueError, AttributeError):
            old_price = 0

        item_data.oldprice = old_price
        return item_data

    def get_max_page_number(self, category):
        url = self.url_pattern.format(page_number=1, page_number_zero=0, **category)
        html = self.download_url(url)
        soup = BeautifulSoup(html, "html.parser")
        try:
            last_span = soup.find('span', {'class': 'last'})
            a_tag = last_span.find('a', {'class': 'pager'})
            max_page = int(a_tag.text)
        except (ValueError, AttributeError):
            logger.warning("Can not fetch max page number for category '%s'", category["category_name"])
            return self.FALLBACK_MAX_PAGE

        return max_page
