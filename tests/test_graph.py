import asyncio

from pydantic import BaseModel

import moirae


class Add(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(1)  # Simulate waiting time

        return self.Output(o=inputs.a + inputs.b)


class Multiply(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        await asyncio.sleep(2)  # Simulate waiting time

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

"""
    t_a = 1
    t_b = 2
    t_c = 1

The execution order should be (a b) -> c
(a b) will run simultaneously, costs max(t_a, t_b) = 2 seconds
Thus the total time should be (max(t_a, t_b)+t_c) = 3 seconds when parallel
If not parallel, the graph will cost sum(t_a, t_b, t_c) = 4 seconds
"""

g = moirae.Graph(graph)
print(g.inputs_schema)
print(g.args_schema)
print(g.outputs_schema)
print(g.data)
print(g.graph.nodes(data=True))
print(g.graph.edges(data=True))



# result = moirae.run(graph)

'''
with Executor(graph) as e:
    while(not e.finished()):
        node_name, output = e.result_queue.get()

        #  Do something with output
'''

'''
async with Executor(graph) as e:
    async for (node_name, output) in e:
        pass
'''