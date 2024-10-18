# Moirae
`Moirae*` is an async workflow execution engine supports static DAGs in `python`.
> *) Moirae are Acient Greek gods. The role of the Moirae was to ensure that every being, mortal and divine, lived out their destiny as it was assigned to them by the laws of the universe.
# Getting Started
## Prerequisites
`Moirae` requires `python>3.8`.
## Developmental Installation
```
git clone https://github.com/lzqlzzq/moirae
pip install -e moirae
```
## Define Node
Node is a basic unit in workflow where the data be transformed. A `Node` class must inherit from `moirae.Node`, which is a subclass of [Pydantic BaseModel](https://docs.pydantic.dev/latest/api/base_model/). The defination of a `Node` class must include:
- An `Input` class: Must inherit from `moirae.Data`. Defines the input data of the node. `moirae.Data` is also a subclass of `pydantic.BaseModel`, so it behaves almost the same as `pydantic.BaseModel`.
- An `Output` class: Must inherit from `moirae.Data`. Defines the output data of the node. `moirae.Data` is also a subclass of `pydantic.BaseModel`, so it behaves almost the same as `pydantic.BaseModel`. Attention the inputs and outputs of the node will be checked by `moirae`.
- An `execute` fuction: Must be an `async` function. Defines how the input data will be transformed to output data. An `Input` instance will be passed into the `execute` function. The arguments of the node can be accessed by `self`.
```[python]
import moirae

class AddMul(moirae.Node):
    # Define input of this node
    class Input(moirae.Data):
        a: float
        b: float

    # Define output of this node
    class Output(moirae.Data):
        o: float

    # Define arguments of this node
    coef: int

    # Define execute of this node, write your logic here
    async def execute(self, inputs: Input) -> Output:
        added = inputs.a + inputs.b         # Make use of the input
        multiplied = self.coef * added      # Make use of the node' s argument
        result = self.Output(o=multiplied)  # Must return a self.Output

        return resutlt
```
Then, it would be registered in `moirae.NODES`:
```[python]
print(moirae.NODES)  # {'AddMul': <class '__main__.AddMul'>}
```
## Execute One Node
You can eagerly execute the node. The result would be returned as the node is successfully executed. `Moirea` will check if the output is match `Node.Output`.
```[python]
# Initialize node instance
add_mul_instance1 = AddMul(coef=2.)

# Initialize input instance of the node
input = AddMul.Input(a=1, b=2)

# Eagar execute the node
output = add_mul_instance1(input)

print(type(output))  # <class '__main__.AddMul.Output'>
print(output.o)      # o=6.0
```
## Build a Graph
Let' define two types of `Node`.
```[python]
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
```
We can build a simple graph with three nodes. The graph is a `dict[node_name: str, node_attr: dict]`.
These attributes must be in `node_attr`:
- `node`: The class name of the `moirae.Node` your defined.
- `arguments`: Arguments of the node.
- `inputs`: The inputs data. `${node_name.node_output_variable_name}` will define a data flow in the graph.
```[python]
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
```
You can show the computation graph:
```
mg = moirae.Graph(graph)

print(mg.graph.nodes(data=True))
print(mg.graph.edges(data=True))

"""
inputs_schema: {}
args_schema: {'a': {'a': FieldInfo(annotation=float, required=True), 'b': FieldInfo(annotation=float, required=True)}, 'b': {'a': FieldInfo(annotation=float, required=True), 'b': FieldInfo(annotation=float, required=True)}}
outputs_schema: {'a': <class '__main__.Add.Output'>, 'b': <class '__main__.Multiply.Output'>, 'c': <class '__main__.Add.Output'>}
input_data: {'a': {'a': 1, 'b': 2}, 'b': {'a': 3, 'b': 2}}
nodes: [('a', {'node': Add(), 'hash': '305dbab2622b17d1c126c74fd9f6fda61dba11f0c9194fc0f703a52ee9e56fccd048b677c11fd4b4c0bf1eea68a7fce6570420b8ac17af92473cbad18154e024'}), ('b', {'node': Multiply(), 'hash': '7e2350d2b67eda7e2b5f6e0d04657fb943c0a87477fc692a9d17f9514b0b227ae6fcd11c6b1be31c2fa3e1a759573ce673ea37d0b55acd1860490d6732525d41'}), ('c', {'node': Add(), 'hash': '3d5d618cb1fc65d25d01f790e04b68a832fd618bb78902b2f5c517a7a284ec967f55cd777ae42d8df06840424129609a553b3731981ab6c813e27e54051413cf'})]
edges: [('a', 'c', {'output_field': 'o', 'input_field': 'b'}), ('b', 'c', {'output_field': 'o', 'input_field': 'a'})]
"""
```
Or visualize it with `networkx` and `matplotlib`:
```[python]
import networkx as nx
import matplotlib.pyplot as plt

nx.draw(mg.graph, with_labels=True)
plt.show()
```
## Async Execution
`moirae` implements a async flow executor. All `Node`s can run as soon as its prerequisites fulfilled **without any waiting**.
```[python]
async def run_graph():
    print(f'[{time()}]: Start executing.')
    async for (node_name, node_output) in moirae.execute_async(mg):
        print(f'[{time()}]{node_name}: {node_output}')
    print(f'[{time()}]: Finish executing.')

if __name__ == "__main__":
    asyncio.run(run_graph())

# [1729154400.537708]: Start executing.
# [1729154401.5393991]a: o=3.0
# [1729154403.541043]b: o=6.0
# [1729154404.5419276]c: o=9.0
# [1729154404.5420897]: Finish executing.
```
## Eager Execution
You can also use `moirae.execute` directly for eager execution.
```[python]
print(moirae.execute(mg)) # {'a': Output(o=3.0), 'b': Output(o=6.0), 'c': Output(o=9.0)}
```
## Cache Mechanism
`moirae` provides a cache mechanism based on topological hashing for storing intermediate results. If the cache hits, `moirae` will try to fetch the data from the cache, avoiding re-run the node. Implement a `moirae.Cache` class like this:
```[python]
import os
import aiofiles


class FileCache(moirae.Cache):
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    async def exists(self, hash_val: str):
        return os.path.exists(os.path.join(self.root_dir, hash_val))

    async def get(self, hash_val: str):
        async with aiofiles.open(os.path.join(self.root_dir, hash_val), mode='rb') as f:
            return await f.read()

    async def put(self, hash_val: str, value: bytes):
        async with aiofiles.open(os.path.join(self.root_dir, hash_val), mode='wb') as f:
            await f.write(value)
```
And execute with `cache` argument:
```[python]
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
```
Will output:
```
Testing execute without cache.
[1729241948.6246948]: Start executing.
[1729241949.6267285]a: o=3.0
[1729241951.6277223]b: o=6.0
[1729241952.6284506]c: o=9.0
[1729241952.6289535]: Finish executing.
Cache is stored!
[1729241952.6298018]: Start executing.
[1729241952.6310601]b: o=6.0
[1729241952.6312633]a: o=3.0
[1729241952.6314924]c: o=9.0
[1729241952.6403558]: Finish executing.
```
The cache is stored at second run. So `moirae` directly fetch outputs from cache instead of running the node.
Remember we defined `Add` node costs 1 second, `Multiply` costs 3 seconds. And if we delete the cache of node `a` and `c`, it will costs only 2 seconds.
# TODO
- Complete unit tests
- Implement gc based on transitive closure and reference count
- Implement subgraph execution
