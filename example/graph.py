import asyncio

import moirae


class Add(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(1)  # Simulate running time

        return self.Output(o=inputs.a + inputs.b)


class Multiply(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(3)  # Simulate running time

        return self.Output(o=inputs.a * inputs.b)


graph = {
    'a': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'a': 1, 'b': 2  # a.o = (1 + 2)
        }
    },
    'b': {
        'node': 'Multiply',
        'arguments': {},
        'inputs': {
            'a': 3, 'b': 2  # b.o = (3 * 2)
        }
    },
    'c': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'a': '${b.o}', 'b': '${a.o}'  # c.o = (b.o + a.o)
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

