from pydantic import BaseModel

import moirae


class Add(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        return self.Output(o=inputs.a + inputs.b)


class Multiply(moirae.Node):
    class Input(moirae.Data):
        a: float
        b: float

    class Output(moirae.Data):
        o: float

    async def execute(self, inputs: Input):
        return self.Output(o=inputs.a * inputs.b)


graph = {
    'a1': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'a': 2, 'b': moirae.Input()
        }
    },
    'b1': {
        'node': 'Add',
        'arguments': {},
        'inputs': {
            'a': 1, 'b': '${a1.o}'
        }
    }
}

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




g = moirae.Graph(graph)
print(g.inputs_schema)
print(g.args_schema)
print(g.outputs_schema)
print(g.data)
print(g.compute_graph.nodes)
print(g.compute_graph.edges(data=True))


