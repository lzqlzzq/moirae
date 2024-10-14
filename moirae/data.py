import hashlib

from pydantic import BaseModel


class Data(BaseModel):
    def __hash__(self):
        return int(hashlib.sha256(
            pickle.dumps((
                sorted(self.__dict__.items())))).hexdigest(), 32)


class Input(Data):
    pass
