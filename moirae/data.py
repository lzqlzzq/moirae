import hashlib

from pydantic import BaseModel

from moirae.hash import stable_hash


class Data(BaseModel):
    def __hash__(self):
        return int(stable_hash(list(self.__dict__.items())).hexdigest(), 32)

