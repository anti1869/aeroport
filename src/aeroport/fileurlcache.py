
"""
This module is for operation on feed data dir and data files. It can download files one-by-one
or simultaneously, check data dir size, clean it, etc.

Feed data dir must be set up in settings.py as FEED_DATA_DIR.
"""

import logging
import os
from typing import Optional
import time

import aiohttp

from aeroport.storage.abc import AbstractStorage, ObjectInStorage
from aeroport.storage.exceptions import ObjectNotFoundException


logger = logging.getLogger(__name__)


class FileUrlCache(object):

    DEFAULT_EXPIRES_SECONDS = 3600 * 12  # 12h
    DOWNLOAD_TIMEOUT = 60 * 30  # 30 min

    def __init__(
            self, storage: AbstractStorage, bucket: str,
            expires: Optional[int] = DEFAULT_EXPIRES_SECONDS):

        """
        Init cache.

        :param storage_config: Storage configuration structure.
        :param bucket: Bucket in storage for this cache instance identification.
        :param expires: Expires timeout for file in seconds.
        """
        self._storage = storage
        self._bucket = bucket
        self._expires = expires
        self._download_hooks = []

    async def get(
            self, url: str, as_filename: str,
            force_download: Optional[bool] = False,
            force_cache: Optional[bool] = False) -> Optional[str]:

        """
        Get cached file, or download it to cache from url.
        If cached file is old it will be downloaded again, unless ``force_cache`` is set

        ``force_download`` have precedence over ``force_cache``.

        :return: Path to the file
        """
        cached_file = None

        if not force_download:
            cached_file = await self.get_cached_file(as_filename, force_cache)

        if cached_file is None and not force_cache:
            try:
                cached_file = await self.download_to_cache(url, as_filename)
            except Exception:
                logger.error("Problem with file downloading", exc_info=True)
                return None

        return cached_file.path if cached_file is not None else None

    async def get_cached_file(
            self, as_filename: str,
            force_cache: Optional[bool] = False) -> Optional[ObjectInStorage]:

        """
        Get file from cache. If its present in cache, but expired (and no ``force_cache`` option,
        will delete file and return None

        :param as_filename: file name
        :param force_cache: if True, will not check expiration timestamp
        :return: Object in storage
        """
        cached_file = None
        try:
            cached_file = await self._storage.fget(self._bucket, as_filename)
            if force_cache:
                return cached_file

            stat = os.stat(cached_file.path)
            if time.time() - stat.st_ctime > self._expires:
                logger.info("Cached file expired")
                cached_file = None
                await self._storage.remove(self._bucket, as_filename)
        except ObjectNotFoundException:
            pass

        return cached_file

    async def download_to_cache(self, url: str, as_filename: str) -> ObjectInStorage:
        logger.info("Downloading to cache, filename=%s", as_filename)
        await self._storage.remove(self._bucket, as_filename)
        async with aiohttp.ClientSession(read_timeout=self.DOWNLOAD_TIMEOUT) as session:
            with aiohttp.Timeout(self.DOWNLOAD_TIMEOUT):
                async with session.get(url, timeout=self.DOWNLOAD_TIMEOUT) as response:
                    assert response.status == 200
                    cached_file = await self._storage.put(self._bucket, as_filename, response)

        for hook in self._download_hooks:
            cached_file = await hook(cached_file)

        return cached_file

    def add_download_hook(self, hook):
        self._download_hooks.append(hook)
