"""
Website scraping, using some scriptable browser like PhantomJS.
"""

import asyncio
from collections import namedtuple
from functools import partial
import logging
from typing import Dict

import aiohttp
from splinter import Browser

from aeroport.abc import (
    AbstractOrigin, AbstractDownloader, AbstractUrlGenerator, AbstractItemAdapter, AbstractPayload,
)
from aeroport.proxy import ProxyCollection


logger = logging.getLogger(__name__)


SchemeItem = namedtuple("SchemeItem", "urlgenerator adapters")


class AiohttpDownloader(AbstractDownloader):

    # TODO: Add proxy usage here

    DEFAULT_TIMEOUT = 15

    async def get_html_from_url(self, url: str) -> str:
        with aiohttp.Timeout(self.timeout):
            response = await aiohttp.get(url)
            assert response.status == 200
            html = await response.text()
        return html

    @property
    def timeout(self) -> int:
        return self.DEFAULT_TIMEOUT


class BrowserDownloader(AbstractDownloader):
    BROWSER_DRIVER = "phantomjs"
    DEFAULT_BROWSER_ARGS = ["--load-images=false"]
    MAX_BROWSERS = 5
    USE_PROXY = False

    def __init__(self):
        super().__init__()
        self._browser = None
        self.sem = asyncio.Semaphore(self.MAX_BROWSERS)
        self.proxy_collection = ProxyCollection()

    @property
    def browser(self) -> Browser:
        if self._browser is None:
            self._browser = self._get_browser()
        return self._browser

    @browser.setter
    def browser(self, value):
        self._browser = value

    def _get_browser(self) -> Browser:
        service_args = self.DEFAULT_BROWSER_ARGS

        if self.USE_PROXY:
            p_address, p_type = self.proxy_collection.get_proxy()
            service_args.append("--proxy={}".format(p_address))
            service_args.append("--proxy-type={}".format(p_type))

        browser = Browser(self.BROWSER_DRIVER, service_args=service_args)
        return browser

    def _download_url_with_browser(self, url) -> str:
        with self._get_browser() as browser:
            logger.info("Fetching %s", url)
            browser.visit(url)
            _ = browser.is_element_not_present_by_tag("body", wait_time=2)

            # For some reason, splinter page analyzing not working, so using BS
            html = browser.html
        return html

    async def get_html_from_url(self, url: str) -> str:
        loop = asyncio.get_event_loop()
        async with self.sem:
            downloader = partial(self._download_url_with_browser, url)
            html = await loop.run_in_executor(None, downloader)
        return html


class ScrapingOrigin(AbstractDownloader, AbstractOrigin):

    SCRAPE_SCHEMES = (
        SchemeItem(
            urlgenerator=AbstractUrlGenerator,
            adapters=(
                (AbstractItemAdapter, {}),
            )
        ),
    )

    async def process(self):
        for scheme in self.SCRAPE_SCHEMES:
            adapters = tuple((cls(**init_kwargs) for cls, init_kwargs in scheme.adapters))
            async for url_info in scheme.urlgenerator():
                html = await self.get_html_from_url(url_info.url)
                for adapter in adapters:
                    for payload in adapter.gen_payload_from_html(html):
                        if payload is not None:
                            self.postprocess_payload(payload, **url_info.kwargs)
                            await self.send_to_destination(payload)

    def postprocess_payload(self, payload: AbstractPayload, **kwargs) -> None:
        pass


class BrowserScrapingOrigin(BrowserDownloader, ScrapingOrigin):
    pass


class AiohttpScrapingOrigin(AiohttpDownloader, ScrapingOrigin):
    pass
