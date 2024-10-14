import re

import networkx as nx

from moirae.node import Node, NODES
from moirae.data import Input


_VAR_NAME_RE = r"[a-zA-Z_]\w*"
# "${NODE_NAME}.{VAR_NAME}"
_REF_RE = re.compile(r"\$\{(" + _VAR_NAME_RE + r").(" + _VAR_NAME_RE + r")\}")

class _GraphFactory:
    def __init__(self, graph):
        self.graph = graph.copy()
        self.compute_graph = nx.MultiDiGraph()
        self.data = {}
        self.inputs_schema = {}
        self.args_schema = {}
        self.outputs_schema = {}

        self._add_nodes()
        self._add_edges()

        assert nx.is_directed_acyclic_graph(self.compute_graph), 'The given graph is not a DAG.'

    def _add_nodes(self):
        for node_name, node_attrs in self.graph.items():
            if(re.match(_VAR_NAME_RE, node_name) is None):
                raise NameError(f"node_name {node_name} is invaild.")

            if(node_attrs['node'] not in NODES):
                raise ValueError(f"Unknown processor node {node_attrs['node']} of node name {node_name}.")

            node_class = NODES[node_attrs['node']]

            try:
                node = node_class.parse_obj(node_attrs['arguments'])
            except:
                raise AttributeError(f'''Cannot initialize node {node_name}.\n
                    Expected schema of arguments is: {node_attrs['node'].schema()}.\n
                    But received: {node_attrs["arguments"]}.''')

            self.outputs_schema[node_name] = node_class.Output
            self.compute_graph.add_node(node_name, node=node)

    def _add_edges(self):
        for node_name, node_attrs in self.graph.items():
            this_node = self.compute_graph.nodes[node_name]['node']
            if(set(node_attrs['inputs'].keys()) != this_node.input_fields.keys()):
                raise ValueError(f"""Input of node {node_name} doesn' t match expected.\n
                    Expected inputs are: {this_node.input_fields}.\n
                    Received inputs are: {set(node_attrs['inputs'].keys())}""")

            for input_name, data in node_attrs['inputs'].items():
                # If the input if an edge
                if(type(data) == str and _REF_RE.match(data)):
                    edge = _REF_RE.match(data)

                    out_node, output_name = edge.groups()
                    out_node_class = self.compute_graph.nodes[out_node]['node']
                    if(out_node not in self.compute_graph.nodes):
                        raise ValueError(f"No <node id={out_node}> referenced by <node id={node_name}>.")

                    if(output_name not in out_node_class.output_fields):
                        raise NameError(f"""Not existed field {output_name} in {out_node_class.Output} referenced by <node id={node_name}>.
                            The output fields of {out_node_class} are {out_node_class.output_fields}""")

                    out_type = out_node_class.output_fields[output_name].annotation
                    in_type = this_node.input_fields[input_name].annotation
                    if(out_type != in_type):
                        raise TypeError(f"""Type of output <node id={out_node}>.{output_name}({in_type}) is not the same as <node id={node_name}>.{in_var_name}({in_type})""")

                    self.compute_graph.add_edge(out_node, node_name, output_name=output_name, input_name=input_name)
                    continue

                # If the input is a dummy input
                if(type(data) == Input):
                    if(node_name not in self.inputs_schema):
                        self.inputs_schema[node_name] = {}

                    self.inputs_schema[node_name][input_name] = this_node.Input.__fields__[input_name]

                    continue

                # If the input is given
                if(node_name not in self.data):
                    self.data[node_name] = {}
                self.data[node_name][input_name] = data

                if(node_name not in self.args_schema):
                    self.args_schema[node_name] = {}
                self.args_schema[node_name][input_name] = this_node.Input.__fields__[input_name]


def Graph(graph: dict):
    return _GraphFactory(graph)


"""
example_graph = {
    "separation1": {
        "node": "SourceSeparation",
        "arguments": {
            "track": "vocals",
            "model": "xxx"
        },
        "inputs": {
            "audio": "DATA......"
            }
        },
    "svc1": {
        "node": "SVC",
        "arguments": {
            "model": "xxx"
        },
        "inputs": {
            "audio": "${seperation1.vocals}"  # Use output from other nodes
            }
        }
    }
"""
