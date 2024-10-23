# `moirae`
`moirae*` is a light-weight async workflow execution engine supports static DAGs in `python`.
> *) Moirae are Acient Greek gods who ensure that every being, mortal and divine, lived out their destiny as it was assigned to them by the laws of the universe.
# Getting Started
## Prerequisites
`moirae` requires `python>=3.8`.

**\*) In `Windows`, please use `python>=3.9` because of a bug related to `asyncio` from python standard library.**
## Installation
### From pypi
```
pip install moirae
```
### From Source
```
git clone https://github.com/lzqlzzq/moirae
pip install -e moirae
```
## Define Node
Node is a basic unit in workflow where the data be transformed. A `Node` class must inherit from `moirae.Node`, which is a subclass of [Pydantic BaseModel](https://docs.pydantic.dev/latest/api/base_model/). The defination of a `Node` class must include:
- An `Input` class: Must inherit from `moirae.Data`. Defines the input data of the node. `moirae.Data` is also a subclass of `pydantic.BaseModel`, so it behaves almost the same as `pydantic.BaseModel`. It should also support `msgpack` protocol for serializing and hashing.
- An `Output` class: Must inherit from `moirae.Data`. Defines the output data of the node. `moirae.Data` is also a subclass of `pydantic.BaseModel`, so it behaves almost the same as `pydantic.BaseModel`. Attention the inputs and outputs of the node will be checked by `moirae`. It should also support `msgpack` protocol for serializing and hashing.
- An `execute` fuction: Must be an `async` function. Defines how the input data will be transformed to output data. An `Input` instance will be passed into the `execute` function. The arguments of the node can be accessed by `self`.
- Optional `arguments`: Define arguments for data transformation in `execute`. `moirae.Node` itself is a subclass of `pydantic.BaseModel`, so it behaves almost the same as `pydantic.BaseModel`. Attention the inputs and outputs of the node will be checked by `moirae`. It should also support `msgpack` protocol for serializing and hashing.
```[python]
import moirae

class AddMul(moirae.Node):
    # Define input of this node
    class Input(moirae.Data):
        x: float
        y: float

    # Define output of this node
    class Output(moirae.Data):
        o: float

    # Define arguments of this node
    coef: int

    # Define execute of this node, write your logic here
    async def execute(self, inputs: Input) -> Output:
        added = inputs.x + inputs.y         # Make use of the input
        multiplied = self.coef * added      # Make use of the node' s argument
        result = self.Output(o=multiplied)  # Must return a self.Output

        return result
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
input = AddMul.Input(x=1, y=2)

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
        await asyncio.sleep(2)  # Simulate running time

        return self.Output(o=inputs.x * inputs.y)
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
```
You can show the computation graph:
```
mg = moirae.Graph(graph)

print(mg.graph.nodes(data=True))
print(mg.graph.edges(data=True))

"""
inputs_schema: {}
args_schema: {'a': {'x': FieldInfo(annotation=float, required=True), 'y': FieldInfo(annotation=float, required=True)}, 'b': {'x': FieldInfo(annotation=float, required=True), 'y': FieldInfo(annotation=float, required=True)}}
outputs_schema: {'a': <class '__main__.Add.Output'>, 'b': <class '__main__.Multiply.Output'>, 'c': <class '__main__.Add.Output'>}
input_data: {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 2}, 'c': {'x': None, 'y': None}}
nodes: [('a', {'node': Add(), 'hash': 'bbdadddac55732cd29aa32d15e88cabdba9d9b064336105838fc57916d8e89a9e208f0b7ddd09d1946093f576f864da3ccf5660d5a25f8bf8ac1faf434acc97d'}), ('b', {'node': Multiply(), 'hash': '84fa63db9acf5dbfd94dd535e61cdcf7cdf8e39046d35a3091e299b1d1663c72df48b8f7a123f7434547a9528c5012021ce6d7b1325435d2a93e5c5f57609f20'}), ('c', {'node': Add(), 'hash': '8a2a9794af9da740059c6e92eed17ff70445babad56dffe646c110b6069903bf563b203feae86ba4fcc00fafb5b80b18da7b82e50a45aecfc4d2499863013bd4'})]
edges: [('a', 'c', {'output_field': 'o', 'input_field': 'y'}), ('b', 'c', {'output_field': 'o', 'input_field': 'x'})]
"""
```
Or visualize it with `networkx` and `matplotlib`:
```[python]
import networkx as nx
import matplotlib.pyplot as plt

nx.draw(mg.graph, with_labels=True)
plt.show()
```
![](/assets/graph.png)
## Async Execution
`moirae` implements a async flow executor. All `Node`s can run **as soon as its prerequisites fulfilled without any waiting**.
```[python]
async def run_graph():
    print(f'[{time()}]: Start executing.')
    async with moirae.Executor(mg) as exe:
        async for (node_name, node_output) in exe:
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
You can also use `moirae.execute` directly to execute the whole graph eagerly.
```[python]
print(f'[{time()}]: Start executing.')
print(moirae.execute(mg))
print(f'[{time()}]: Finish executing.')

# [1729492804.0473106]: Start executing.
# {'a': Output(o=3.0), 'b': Output(o=6.0), 'c': Output(o=9.0)}
# [1729492808.0519385]: Finish executing.
```
## Cache Mechanism
`moirae` provides a cache mechanism based on topological hashing for storing intermediate results. If the cache hits, `moirae` will try to fetch the data from the cache, avoiding re-run the node. Implement a `moirae.Cache` class like this:
```[python]
import os
import aiofiles  # pip install aiofiles

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
```
These three async method: `exists`, `get`, `put` must be implemented for a `moirae.Cache` class.
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
Remember we defined `Add` node costs 1 second, `Multiply` costs 3 seconds. For example if we modify the input of node `a`, it will reuse the output of node `b`, only execute node `a` and `c`, thus only costs 2 seconds.
# TODO
- Complete unit tests
- Implement subgraph execution
