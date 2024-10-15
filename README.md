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
```
Or visualize it with `networkx` and `matplotlib`:
```[python]
import networkx as nx
import matplotlib.pyplot as plt

nx.draw(mg.graph, with_labels=True)
plt.show()
```
