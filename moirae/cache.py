from abc import ABC, abstractmethod

from moirae import Data


class Cache(ABC):

    @abstractmethod
    async def exists(self, hash_val: str):
        raise NotImplementedError(f'"exist" method of {self.__class__} is not implemented!')

    @abstractmethod
    async def get(self, hash_val: str):
        raise NotImplementedError(f'"get" method of {self.__class__} is not implemented!')

    @abstractmethod
    async def put(self, hash_val: str, value: bytes):
        raise NotImplementedError(f'"put" method of {self.__class__} is not implemented!')


class CacheIOError(IOError):
    pass