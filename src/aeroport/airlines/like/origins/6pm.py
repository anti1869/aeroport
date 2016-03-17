"""
Adapter for the 6pm.com items feed. Based on zappos.com, as latter is actually owner of this company.
"""

import logging

from aeroport.scraping import (
    SchemeItem,
)
from aeroport.airlines.like.origins.zappos import ZapposItemAdapter, ZapposUrlGenerator, Origin as ZapposOrigin
from aeroport.airlines.like.payload import ShopItem


logger = logging.getLogger(__name__)

SHOP_TITLE = "6pm"
SHOP_NAME = "6pm"
SHOP_URL = "http://6pm.com"


class The6pmUrlGenerator(ZapposUrlGenerator):

    url_pattern = "%s/{category_name}{code1}#!/" \
                  "{category_name_page}-page{page_number}/{code2}.zso?p={page_number_zero}" % SHOP_URL

    category_mapping = (
        {
            "category_name": "handbags",
            "category_name_page": "handbags",
            "code1": "~4P",
            "code2": "COjWARCS1wHiAgIBAg",
            "matching_category_id": 1,
        },
        {
            "category_name": "backpacks",
            "category_name_page": "backpacks",
            "code1": "~1N",
            "code2": "COjWARCQ1wHiAgIBAg",
            "matching_category_id": 2,
        },
        {
            "category_name": "luggage-bags",
            "category_name_page": "luggage",
            "code1": "~5",
            "code2": "COjWARCT1wHiAgIBAg",
            "matching_category_id": 3,
        },
        {
            "category_name": "wallets-accessories",
            "category_name_page": "wallets-accessories",
            "code1": "~2",
            "code2": "COjWARCW1wHiAgIBAg",
            "matching_category_id": 4,
        },
        {
            "category_name": "duffle-bags",
            "category_name_page": "duffle-bags",
            "code1": "~3",
            "code2": "COjWARCj1wHiAgIBAg",
            "matching_category_id": 5,
        },
        {
            "category_name": "messenger-bags",
            "category_name_page": "messenger-bags",
            "code1": "~L",
            "code2": "COjWARCU1wHiAgIBAg",
            "matching_category_id": 6,
        },
        {
            "category_name": "laptop-bags",
            "category_name_page": "laptop-bags",
            "code1": "~L",
            "code2": "COjWARCY1wHiAgIBAg",
            "matching_category_id": 7,
        },
    )


class The6pmItemAdapter(ZapposItemAdapter):

    PRICE_CLASS = "price-6pm"

    _shop_url = SHOP_URL
    _shop_title = SHOP_TITLE
    _shop_name = SHOP_NAME


class Origin(ZapposOrigin):

    SCRAPE_SCHEMES = (
        SchemeItem(
            urlgenerator=The6pmUrlGenerator,
            adapters=(
                (The6pmItemAdapter, {}),
            )
        ),
    )

    _shop_title = SHOP_TITLE
    _shop_name = SHOP_NAME

    @property
    def name(self) -> str:
        return "6pm"
