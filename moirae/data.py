import hashlib
import pickle

from pydantic import BaseModel

from moirae.hash import stable_hash


class Data(BaseModel):
    def __hash__(self):
        return int(stable_hash(self), 32)

