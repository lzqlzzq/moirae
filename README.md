# Moirae
`Moirae*` is an async workflow execution engine supports both dynamic and static DAGs in `python`.
> *) The role of the Moirai was to ensure that every being, mortal and divine, lived out their destiny as it was assigned to them by the laws of the universe.
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

