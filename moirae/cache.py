from abc import ABC, abstractmethod

from moirae import Data


class Cache(ABC):

    @abstractmethod
    async def exists(self, hash_key: str):
        raise NotImplementedError(f'"exists" method of {self.__class__} is not implemented!')

    @abstractmethod
    async def get(self, hash_key: str):
        raise NotImplementedError(f'"get" method of {self.__class__} is not implemented!')

    @abstractmethod
    async def put(self, hash_key: str, data_value: bytes):
        raise NotImplementedError(f'"put" method of {self.__class__} is not implemented!')


class CacheIOError(IOError):
    pass
