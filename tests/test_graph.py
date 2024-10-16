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
        await asyncio.sleep(2)  # Simulate running time

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

g = moirae.Graph(graph)
print('inputs_schema: ', g.inputs_schema)
print('args_schema:', g.args_schema)
print('outputs_schema:', g.outputs_schema)
print('input_data:', g.input_data)
print('nodes:', g.graph.nodes(data=True))
print('edges:', g.graph.edges(data=True))

