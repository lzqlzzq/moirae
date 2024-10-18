import hashlib
import pickle

from pydantic import BaseModel

from moirae.hash import stable_hash


class Data(BaseModel):
    @property
    def hash(self):
        return stable_hash(self.__dict__.items())

