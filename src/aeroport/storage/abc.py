from abc import ABCMeta, abstractmethod
from collections import namedtuple
from asyncio import AbstractEventLoop, get_event_loop
import logging
from typing import BinaryIO, Iterable, Optional

ObjectInStorage = namedtuple('ObjectInStorage', 'filename path url')


class AbstractStorage(object, metaclass=ABCMeta):
    def __init__(self, loop: AbstractEventLoop = None, *args, **kwargs):
        self._logger = logging.getLogger('__name__')

        self._loop = loop
        if self._loop is None:
            self._loop = get_event_loop()

    @abstractmethod
    async def put(self, bucket_name: str, object_name: str, data: BinaryIO) -> ObjectInStorage:
        """
        Upload an object

        :param bucket_name: Name of the bucket
        :param object_name: Name of the object
        :param data: Contents to upload

        :return: Object in storage
        """

    @abstractmethod
    async def fput(self, bucket_name: str, object_name: str, file_path: str) -> ObjectInStorage:
        """
        Uploads the object using contents from a file

        :param bucket_name: Name of the bucket
        :param object_name: Name of the object
        :param file_path: File path of the file to be uploaded

        :return: Object in storage
        """

    @abstractmethod
    async def list(self, bucket_name: str) -> Iterable[ObjectInStorage]:
        """
        List objects in a storage

        :param bucket_name: Name of the bucket

        :return: All the objects in the storage
        """

    @abstractmethod
    async def get(self, bucket_name: str, object_name: str) -> BinaryIO:
        """
        Download object

        :param bucket_name: Name of the bucket
        :param object_name: Name of the object

        :return: Data for represents object reader
        """

    @abstractmethod
    async def fget(self, bucket_name: str, object_name: str, file_path: Optional[str] = None) -> ObjectInStorage:
        """
        Download an object

        :param bucket_name: Name of the bucket
        :param object_name: Name of the object
        :param file_path: File path. If not specified, temporary file will be used (implementation-specific).
        """

    @abstractmethod
    async def remove(self, bucket_name: str, object_name: str):
        """
        Remove an object from the storage

        :param bucket_name: Name of the bucket
        :param object_name: Name of object to remove
        """
