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
    async for (node_name, node_output) in moirae.execute_async(mg):
        print(f'[{time()}]{node_name}: {node_output}')
    print(f'[{time()}]: Finish executing.')


def execute_graph():
    mg = moirae.Graph(graph)

    print(f'[{time()}]: Start executing.')
    print(moirae.execute(mg))
    print(f'[{time()}]: Finish executing.')


if __name__ == "__main__":
    print('Testing async execute.')
    asyncio.run(execute_graph_async())

    print('')
    print('Testing sync execute.')
    execute_graph()
