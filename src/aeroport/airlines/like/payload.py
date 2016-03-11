"""
Payload definitions. It is basically a schema for collected data.
"""

from aeroport.payload import Payload, Field


class ShopItem(Payload):
    original_id = Field()
    url = Field()
    thumbnail_url = Field()
    brand_title = Field()
    title = Field()
    price = Field()
    oldprice = Field()
    discount = Field()
    brand_id = Field()
    shop_title = Field()
    shop_name = Field()
    origin = Field()
    primary_local_category_id = Field()
    category_name = Field()

    def postprocess(self, **kwargs):
        self["primary_local_category_id"] = kwargs.get("primary_local_category_id", None)
        self["category_name"] = kwargs.get("category_name", None)
        self["discount"] = round(100 - round(100 * self["price"] / self["oldprice"])) if self["oldprice"] else 0


class Brand(Payload):
    title = Field()
    logo_url = Field()
