"""
Example origin. Will scrape repo list from configured user.
"""

from asyncio import ensure_future

import aiohttp
from bs4 import BeautifulSoup

from aeroport.abc import AbstractOrigin
from aeroport.airlines.air_example.payload import Repo
from aeroport.destinations.console import ConsoleDestination


START_PAGE = "https://github.com/anti1869?tab=repositories"


class Origin(AbstractOrigin):
    @property
    def default_destination(self):
        return ConsoleDestination()

    async def process(self):
        async with aiohttp.get(START_PAGE) as response:
            assert response.status == 200
            data = await response.read()

        soup = BeautifulSoup(data, "html.parser")
        for repo in soup.find_all("div", {"class": "repo-list-item"}):
            r = Repo()
            r["title"] = repo.find("h3", {"class": "repo-list-name"}).text.strip()
            r["description"] = repo.find("p", {"class": "repo-list-description"}).text.strip()
            ensure_future(
                self.send_to_destination(r)
            )
