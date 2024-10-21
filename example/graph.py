import asyncio

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

mg = moirae.Graph(graph)
print('inputs_schema:', mg.inputs_schema)
print('args_schema:', mg.args_schema)
print('outputs_schema:', mg.outputs_schema)
print('input_data:', mg.input_data)
print('nodes:', mg.graph.nodes(data=True))
print('edges:', mg.graph.edges(data=True))


import networkx as nx
import matplotlib.pyplot as plt


nx.draw(mg.graph, with_labels=True)
plt.show()

