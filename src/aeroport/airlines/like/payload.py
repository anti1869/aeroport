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
    # long_id
    brand_id = Field()
    shop_title = Field()
    shop_name = Field()
    primary_local_category_id = Field()
    category_name = Field()


class ShopItemPostprocessMixin(object):

    def postprocess_payload(self, payload: ShopItem, **kwargs) -> None:
        payload["primary_local_category_id"] = kwargs.get("primary_local_category_id", None)
        payload["category_name"] = kwargs.get("category_name", None)
        payload["shop_title"] = getattr(self, "_shop_title")
        payload["shop_name"] = getattr(self, "_shop_name")
        payload["discount"] = round(100 - round(100 * payload["price"] / payload["oldprice"])) \
            if payload["oldprice"] else 0