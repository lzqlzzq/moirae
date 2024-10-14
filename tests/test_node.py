from pydantic import BaseModel

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

    # Define execute of this node
    async def execute(self, inputs: Input) -> Output:
        return self.Output(o=(inputs.a + inputs.b) * self.coef)


def test_node():
    print(moirae.NODES)
    # Initialize node instance
    add_mul_instance1 = AddMul(coef=2.)

    # Initialize input instance of the node
    input = AddMul.Input(a=1, b=2)

    # Eagar execute the node
    output = add_mul_instance1(input)

    # Print output
    print(type(output))
    print(output)

