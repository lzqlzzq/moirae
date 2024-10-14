from abc import ABC, abstractmethod
import pickle
import hashlib
import inspect
import asyncio

from pydantic import BaseModel

from moirae import Data


NODES = {}


class Node(BaseModel, ABC):

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        if(cls.__name__ in NODES):
            raise NameError(f'Node name "{cls.__name__}" duplicated!')

        NODES[cls.__name__] = cls

        super().__init_subclass__(*args, **kwargs)

        if('Input' not in cls.__dict__):
            raise NotImplementedError(f"Input format of the node {cls} is not defined!")
        if('Output' not in cls.__dict__):
            raise NotImplementedError(f"Output format of the node {cls} is not defined!")

        if(not issubclass(cls.__dict__['Input'], Data)):
            raise TypeError(f"Input of the node {cls} must be a concflow.Data!")
        if(not issubclass(cls.__dict__['Output'], Data)):
            raise TypeError(f"Output of the node {cls} must be a concflow.Data!")

        cls._signature = hashlib.sha256((
            cls.__class__.__name__ + \
            str(sorted(cls.__dict__.keys())) + \
            str(sorted(cls.Input.__dict__.keys())) + \
            str(sorted(cls.Output.__dict__.keys())) + \
            inspect.getsource(cls.execute)).encode('utf-8')).hexdigest()

    @abstractmethod
    async def execute(self):
        raise NotImplementedError(f"The method <execute> must be implemented for {self.__class__}!")

    def check_inputs(self, inputs):
        if(type(inputs) != self.Input):
            raise TypeError(f"Input type({type(inputs)}) must be {self.Input}.")

    def check_outputs(self, outputs):
        if(type(outputs) != self.Output):
            raise TypeError(f"Output type({type(outputs)}) must be {self.Output}. Please check the impelmentation of the node.")

    def __call__(self, inputs):
        self.check_inputs(inputs)
        outputs = asyncio.run(self.execute(inputs))
        self.check_outputs(outputs)

        return outputs

    def __hash__(self):
        return int(hashlib.sha256(pickle.dumps((
                    self._signature,
                    sorted(self.__dict__.values())))).hexdigest(), 32)

    @property
    def input_fields(self):
        return self.Input.__fields__

    @property
    def output_fields(self):
        return self.Output.__fields__

