"""
Payload definitions. It is basically a schema for collected data.
"""

from aeroport.payload import Payload, Field


class ShopItem(Payload):
    original_id = Field()
    url = Field()
    thumbnail_uri = Field()
    brand_title = Field()
    title = Field()
    price = Field()
    oldprice = Field()
    discount = Field()
    # shop_id
    # long_id
    brand_id = Field()
    shop_title = Field()
    primary_local_category_id = Field()