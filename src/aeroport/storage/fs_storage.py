import os
import shutil
from functools import partial
from typing import BinaryIO, Iterable, Optional

from aeroport.storage.abc import AbstractStorage, ObjectInStorage
from aeroport.storage import storage_executor
from aeroport.storage import exceptions


class FileSystemStorage(AbstractStorage):

    SIZE_DIVIDER_NAME = 2

    def __init__(self, url_template: str, storage_path: str, fs_nesting_depth: int = 2, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._url_template = url_template
        self._storage_path = storage_path
        self._check_datadir(self._storage_path)
        self._fs_nesting_depth = fs_nesting_depth

    def _check_datadir(self, storage_path: str):
        """
        Ensure that storage dir exists and create it if it's not.

        :return: Doesn't return anything
        """
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def _generate_inner_path(self, object_name: str) -> str:
        """
        Generate path nested directories

        :param object_name: Object name

        :return: Path nested directories
        """

        dirs = (object_name[level:level + self.SIZE_DIVIDER_NAME] for level in
                range(0, self._fs_nesting_depth * self.SIZE_DIVIDER_NAME, self.SIZE_DIVIDER_NAME))

        path = os.path.join(*dirs)
        return path

    def _make_url(self, bucket_name: str, object_name: str) -> str:
        if self._url_template is None:
            return
        url = self._url_template.format(
            bucket_name=bucket_name,
            paths=self._generate_inner_path(object_name),
            filename=object_name,
        )
        return url

    def _make_full_path(self, bucket_name: str, object_name: str) -> str:
        full_path = os.path.join(self._storage_path, bucket_name, self._generate_inner_path(object_name))
        if not os.path.isdir(full_path):
            os.makedirs(full_path)

        full_path_file = os.path.join(full_path, object_name)
        return full_path_file

    def _remove_object(self, object_path: str):
        if os.path.isfile(object_path):
            os.remove(object_path)

    async def remove(self, bucket_name: str, object_name: str):
        fn_remove = partial(
            self._remove_object,
            object_path=self._make_full_path(bucket_name, object_name),
        )
        await self._loop.run_in_executor(storage_executor, fn_remove)

    def _list_objects(self, storage_path: str) -> Iterable[str]:
        for root, _, files in os.walk(storage_path):
            for filename in files:
                yield filename

    async def list(self, bucket_name: str) -> Iterable[ObjectInStorage]:
        fn_list = partial(
            self._list_objects,
            storage_path=os.path.join(self._storage_path, bucket_name),
        )
        objects = await self._loop.run_in_executor(storage_executor, fn_list)
        objects_map = map(lambda o: ObjectInStorage(
            filename=o, path=self._make_full_path(bucket_name, o),url=self._make_url(bucket_name, o), ), objects)
        return objects_map

    async def put(self, bucket_name: str, object_name: str, data: BinaryIO) -> ObjectInStorage:
        object_path = self._make_full_path(bucket_name, object_name)
        size = 0
        with open(object_path, 'wb') as f:
            while True:
                # TODO: aiohttp > 1.0
                # chunk = await file_data.read_chunk()
                # TODO: Distinguish between aiohttp and generic (if there is content present)
                chunk = await data.content.read(8096)
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)

        result = ObjectInStorage(
            filename=object_name,
            path=self._make_full_path(bucket_name, object_name),
            url=self._make_url(bucket_name, object_name)
        )
        return result

    def _fput_object(self, object_path: str, file_path: str):
        shutil.copy(file_path, object_path)

    async def fput(self, bucket_name: str, object_name: str, file_path: str) -> ObjectInStorage:
        fn_fput = partial(
            self._fput_object,
            object_path=self._make_full_path(bucket_name, object_name),
            file_path=file_path,
        )
        await self._loop.run_in_executor(storage_executor, fn_fput)
        return ObjectInStorage(
            filename=object_name,
            path=self._make_full_path(bucket_name, object_name),
            url=self._make_url(bucket_name, object_name)
        )

    async def get(self, backet_name: str, object_name: str) -> BinaryIO:
        raise NotImplementedError()

    async def fget(self, bucket_name: str, object_name: str, file_path: Optional[str] = None) -> ObjectInStorage:
        """
        Get file from storage. If ``file_path`` is not specified, will return link to the file in storage.
        If ``file_path`` exist, will copy that file from storage.
        """
        object_path = self._make_full_path(bucket_name, object_name)
        if not os.path.exists(object_path):
            raise exceptions.ObjectNotFoundException

        # TODO: Implement copy
        result = ObjectInStorage(
            filename=object_name,
            path=object_path,
            url=self._make_url(bucket_name, object_name)
        )
        return result
