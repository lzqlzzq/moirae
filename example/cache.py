import asyncio
from time import time

import moirae


class Add(moirae.Node):
    class Input(moirae.Data):
        x: float
        y: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(1)  # Simulate running time

        return self.Output(o=inputs.x + inputs.y)


class Multiply(moirae.Node):
    class Input(moirae.Data):
        x: float
        y: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(3)  # Simulate running time

        return self.Output(o=inputs.x * inputs.y)


import os
import aiofiles


class FileCache(moirae.Cache):
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    async def exists(self, hash_key: str):
        return os.path.exists(os.path.join(self.root_dir, hash_key))

    async def get(self, hash_key: str):
        async with aiofiles.open(os.path.join(self.root_dir, hash_key), mode='rb') as f:
            return await f.read()

    async def put(self, hash_key: str, data_value: bytes):
        async with aiofiles.open(os.path.join(self.root_dir, hash_key), mode='wb') as f:
            await f.write(data_value)


graph = {
    'a': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'x': 1, 'y': 2  # a.o = (1 + 2)
        }
    },
    'b': {
        'node': 'Multiply',
        'arguments': {},
        'inputs': {
            'x': 3, 'y': 2  # b.o = (3 * 2)
        }
    },
    'c': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'x': '${b.o}', 'y': '${a.o}'  # c.o = (b.o + a.o)
        }
    }
}


async def execute_graph_async():
    mg = moirae.Graph(graph)

    print(f'[{time()}]: Start executing.')
    async for (node_name, node_output) in moirae.execute_async(mg, FileCache(".")):
        print(f'[{time()}]{node_name}: {node_output}')
    print(f'[{time()}]: Finish executing.')


if __name__ == "__main__":
    print('Testing execute without cache.')
    asyncio.run(execute_graph_async())

    print('Cache is stored!')
    asyncio.run(execute_graph_async())

