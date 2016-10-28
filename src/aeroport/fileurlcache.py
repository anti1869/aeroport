
"""
This module is for operation on feed data dir and data files. It can download files one-by-one or simultaneously,
check data dir size, clean it, etc.

Feed data dir must be set up in settings.py as FEED_DATA_DIR.
"""

import logging
import os
from typing import Dict, Optional
import time

import aiohttp

from sunhead.utils import get_class_by_path

from aeroport.storage.abc import AbstractStorage, ObjectInStorage
from aeroport.storage.exceptions import ObjectNotFoundException


logger = logging.getLogger(__name__)


class FileUrlCache(object):

    DEFAULT_EXPIRES_SECONDS = 3600 * 12  # 12h
    DOWNLOAD_TIMEOUT = 60 * 30  # 30 min

    def __init__(self, storage: AbstractStorage, bucket: str, expires: Optional[int] = DEFAULT_EXPIRES_SECONDS):
        """
        Init cache.

        :param storage_config: Storage configuration structure.
        :param bucket: Bucket in storage for this cache instance identification.
        :param expires: Expires timeout for file in seconds.
        """
        self._storage = storage
        self._bucket = bucket
        self._expires = expires

    async def get(self, url: str, as_filename: str, force_download: Optional[bool] = False) -> str:
        """
        Get cached file, or download it to cache from url. If cached file is old it will be downloaded again.

        :return: Path to the file
        """
        cached_file = None

        if not force_download:
            cached_file = await self.get_cached_file(as_filename)

        if cached_file is None:
            try:
                cached_file = await self.download_to_cache(url, as_filename)
            except Exception:
                logger.error("Problem with file downloading", exc_info=True)
                return None

        return cached_file.path

    async def get_cached_file(self, as_filename: str):
        cached_file = None
        try:
            cached_file = await self._storage.fget(self._bucket, as_filename)
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
        async with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(self.DOWNLOAD_TIMEOUT):
                async with session.get(url) as response:
                    assert response.status == 200
                    cached_file = await self._storage.put(self._bucket, as_filename, response)
        return cached_file


#
#
#
# from django.conf import settings
# from urllib.request import urlopen
# import os
# import tempfile
# import zipfile
# import sys
# from redpig.catalogue.models import FeedRecord
# from redpig.catalogue.utils import MultiDownload
#
#
#
#
#
# def clean_feeddatadir(verbose=True):
#     """
#     Remove all files that is not belong to feedrecord from feed_data_dir.
#     Usually it cleans it out of broken incomplete downloads.
#
#     :param verbose: Wheter to print diagnostic messages.
#     :return: Doesn't return anything
#     """
#     check_feeddatadir()
#     feed_list = set(["%s.xml" % n for n in FeedRecord.objects.all().values_list('name', flat=True)])
#     present_files = set(os.listdir(settings.FEED_DATA_DIR))
#     remove_files = present_files - feed_list
#     for filename in remove_files:
#         try:
#             os.remove(os.path.join(settings.FEED_DATA_DIR, filename))
#         except OSError as e:
#             if verbose:
#                 print(e)
#     if verbose:
#         print("%s files deleted" % len(remove_files))
#
#
# def print_feedlist(shop_id=None):
#     """
#     Print info about feed list to stdout. If ``shop_id`` is specified, print info only about this shop feed.
#
#     :param shop_id: If it is specified, info only about that shop FeedRecord will be printed.
#     """
#     feed_list = FeedRecord.objects.exclude(pk=0)
#     if shop_id is not None:
#         feed_list = feed_list.filter(shop_id=shop_id)
#     check_feeddatadir()
#     for feed in feed_list.order_by('id'):
#         feed_filename = os.path.join(settings.FEED_DATA_DIR, "%s.xml" % feed.name)
#         if os.path.isfile(feed_filename):
#             feed_fileinfo = "%.2f Mb" % (float(os.path.getsize(feed_filename)) / 1024.0 / 1024.0)
#         else:
#             feed_fileinfo = "NOT EXIST"
#         print("%s, shop_id=%s, local_file=%s, %s" % (feed.name, feed.shop_id, feed_fileinfo, feed.data_source))
#
#
# def download_http_function(url, *args):
#     """
#     Worker function incapsulation for multithreaded downloader. Just converts *args and calls actual function.
#
#     :param url: url to download.
#     :param args: Arguments, passed by MultiDownloader class instance.
#     :return: Whatever actual function does.
#     """
#     filename = args[0]
#     return download_http(url, filename, verbose=False)
#
#
# def download_http(url, filename, verbose=True):
#     """
#     Load file from http data source. There is support for zip file, which will be decompressed.
#     Downloaded and decompressed file will be renamed to ``filename``, so specify final extension in that argument.
#
#     :param filename: You need to specify only basename here (ex. ``lamoda.xml``). Full path will be automatically \
#                     constructed based on FEED_DATA_DIR setting
#     :param verbose: If ``True``, method will print progress information to stdout.
#     :return: Doesn't return any value.
#     """
#     if verbose:
#         print("Updating from %s" % url)
#     response = urlopen(url)
#     __, extension = os.path.splitext(url)  # Get extension of the data_source file
#     if extension == '':  # Assume that it is xml feed by default
#         extension = 'xml'
#     extension = extension.lstrip(".")
#     check_feeddatadir()
#     # Get temporary file name
#     tmp_filename = os.path.join(settings.FEED_DATA_DIR, "%s.%s" % (next(tempfile._get_candidate_names()), extension))
#     feed_filename = os.path.join(settings.FEED_DATA_DIR, filename)
#
#     # Do download
#     downloaded = 0
#     chunk_size = 256 * 10240
#     with open(tmp_filename, 'wb') as fp:
#         while True:
#             chunk = response.read(chunk_size)
#             downloaded += len(chunk)
#             if verbose:
#                 sys.stdout.write("Downloaded %.2f Mb\r" % ((float(downloaded) / 1024.0) / 1024.0))
#                 sys.stdout.flush()
#             if not chunk:
#                 break
#             fp.write(chunk)
#     if verbose:
#         print("")
#
#     # Check whether it is zip file
#     if extension == "zip":
#         # Decompress zip onto the feed file and remove temp file
#         zfile = zipfile.ZipFile(tmp_filename)
#         name = zfile.namelist()[0]
#         if verbose:
#             print("Decompressing...")
#         with open(feed_filename, "wb") as fd:
#             fd.write(zfile.read(name))
#         os.remove(tmp_filename)
#     else:  # Else move it on the place of original file
#         if os.path.isfile(feed_filename):
#             os.remove(feed_filename)
#         os.rename(tmp_filename, feed_filename)
#
#
# def download_multiple(exclude_id=None):
#     """
#     Download several shop feeds at one using multiple threads. By default feeds for all shops will be downloaded.
#
#     :param exclude_id: List of ``shop_id`` to exclude.
#     """
#     downloader = MultiDownload(download_http_function)
#     url_list = [
#         (feedrecord.data_source, tuple(["%s.xml" % feedrecord.name]))
#         for feedrecord in FeedRecord.objects.exclude(shop_id__in=[] if exclude_id is None else exclude_id)
#         ]
#     downloader.download(url_list)
