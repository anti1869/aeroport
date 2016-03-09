"""
Website scraping, using some scriptable browser like PhantomJS.
"""

import asyncio
from collections import Iterable, AsyncIterable, namedtuple
from functools import partial
import logging

from splinter import Browser

from aeroport.abc import AbstractOrigin, AbstractPayload
from aeroport.proxy import ProxyCollection


logger = logging.getLogger(__name__)


SchemeItem = namedtuple("SchemeItem", "urlgenerator adapters")


class UrlGenerator(AsyncIterable):
    async def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self.fetch_data()
        if data:
            return data
        else:
            raise StopAsyncIteration

    async def fetch_data(self):
        return None


class ItemAdapter(object):

    def gen_payload_from_html(self, html):
        raw_items = self.extract_raw_items_from_html(html)
        return map(self.adapt_raw_item, raw_items)

    def extract_raw_items_from_html(self, html):
        return []

    def adapt_raw_item(self, raw_item) -> AbstractPayload:
        return None



class BrowserScraper(AbstractOrigin):

    BROWSER_DRIVER = "phantomjs"
    DEFAULT_BROWSER_ARGS = ["--load-images=false"]
    MAX_BROWSERS = 5
    USE_PROXY = False

    FALLBACK_MAX_PAGE = 1

    SCRAPE_SCHEMES = (
        SchemeItem(
            urlgenerator=UrlGenerator,
            adapters=(
                (ItemAdapter, {}),
            )
        ),
    )

    def __init__(self):
        super().__init__()
        self._browser = None
        self.sem = asyncio.Semaphore(self.MAX_BROWSERS)
        self.proxy_collection = ProxyCollection()

    async def process(self):
        for scheme in self.SCRAPE_SCHEMES:
            adapters = tuple((cls(**init_kwargs) for cls, init_kwargs in scheme.adapters))
            async for url in scheme.urlgenerator():
                html = await self.get_html_from_url(url)
                for adapter in adapters:
                    for payload in adapter.gen_payload_from_html(html):
                        await self.send_to_destination(payload)


    @property
    def browser(self) -> Browser:
        if self._browser is None:
            self._browser = self.get_browser()
        return self._browser

    @browser.setter
    def browser(self, value):
        self._browser = value

    def get_browser(self) -> Browser:
        service_args = self.DEFAULT_BROWSER_ARGS

        if self.USE_PROXY:
            p_address, p_type = self.proxy_collection.get_proxy()
            service_args.append("--proxy={}".format(p_address))
            service_args.append("--proxy-type={}".format(p_type))

        browser = Browser(self.BROWSER_DRIVER, service_args=service_args)
        return browser

    def download_url_with_browser(self, url) -> str:
        with self.get_browser() as browser:

            logger.info("Fetching %s", url)
            browser.visit(url)
            _ = browser.is_element_not_present_by_tag("body", wait_time=2)

            # For some reason, splinter page analyzing not working, so using BS
            html = browser.html
        return html

    def get_max_page_number(self, category):
        return 0

    async def get_html_from_url(self, url: str) -> str:
        loop = asyncio.get_event_loop()
        async with self.sem:
            downloader = partial(self.download_url_with_browser, url)
            html = await loop.run_in_executor(None, downloader)
        return html

    # def iter_categories(self):
    #     for category in self.category_mapping:
    #         logger.info("Processing category '%s'", category["category_name"])
    #         yield category

    # def iter_category_pages(self, category):
    #     max_page_number = self.get_max_page_number(category)
    #     for page_number in range(1, max_page_number + 1):
    #         yield page_number

    # def get_category_page_url(self, category, page_number):
    #     category['page_number'] = str(page_number)
    #     category['page_number_zero'] = str(page_number - 1)
    #     url = self.url_pattern.format(**category)
    #     return url
    #
    # @asyncio.coroutine
    # def get_items_on_page(self, category, page_number):
    #     url = self.get_category_page_url(category, page_number)
    #
    #     raw_items_data = yield from self.extract_raw_items_from_url(url)
    #     adapt_raw_item = partial(self.adapt_raw_item, category=category)
    #     item_list = map(adapt_raw_item, raw_items_data)
    #     return item_list
    #
    # def adapt_raw_item(self, raw_item, **kwargs):
    #     return None
    #
    # @asyncio.coroutine
    # def extract_raw_items_from_url(self, url):
    #     return []
    #
    # @asyncio.coroutine
    # def process_page(self, category, page):
    #     logger.info("Processing category %s page %s", category["category_name"], page)
    #     item_list = yield from self.get_items_on_page(category, page)
    #     logger.info("Finished processing category %s page %s", category["category_name"], page)
    #     return item_list
    #
    # def iter_items_on_page(self, category, page):
    #     raise StopIteration