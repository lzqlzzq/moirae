import re
import hashlib
from copy import deepcopy

import networkx as nx

from moirae.node import Node, NODES
from moirae.hash import stable_hash


_VAR_NAME_RE = r"[a-zA-Z_]\w*"
# "${NODE_NAME}.{VAR_NAME}"
_REF_RE = re.compile(r"\$\{(" + _VAR_NAME_RE + r").(" + _VAR_NAME_RE + r")\}")


class Graph:
    def __init__(self, graph):
        self.graph = nx.MultiDiGraph()
        self.input_data = {}

        self.inputs_schema = {}
        self.args_schema = {}
        self.outputs_schema = {}

        self.hashes = {}

        # Build graph
        self._add_nodes(graph)
        self._add_edges(graph)

        assert nx.is_directed_acyclic_graph(self.graph), 'The given graph is not a DAG.'

        self._build_merkle_tree()

    def _add_nodes(self, graph):
        for node_name, node_attrs in graph.items():
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
            self.graph.add_node(node_name, node=node)

    def _add_edges(self, graph):
        for node_name, node_attrs in graph.items():
            this_node = self.graph.nodes[node_name]['node']

            # Check if the input matches the input defination
            if(set(node_attrs['inputs'].keys()) != this_node.input_fields.keys()):
                raise ValueError(f"""Input of node {node_name} doesn' t match expected.\n
                    Expected inputs are: {this_node.input_fields}.\n
                    Received inputs are: {set(node_attrs['inputs'].keys())}""")

            for input_field, data in node_attrs['inputs'].items():

                # Not support dummy input for now.
                """
                # Handle dummy input
                if(type(data) == Input):
                    if(node_name not in self.inputs_schema):
                        self.inputs_schema[node_name] = {}

                    self.inputs_schema[node_name][input_field] = this_node.Input.__fields__[input_field]

                    continue
                """


                # Handle edge
                if(type(data) == str and _REF_RE.match(data)):
                    edge = _REF_RE.match(data)

                    out_node, output_field = edge.groups()
                    out_node_class = self.graph.nodes[out_node]['node']
                    if(out_node not in self.graph.nodes):
                        raise ValueError(f"No <node id={out_node}> referenced by <node id={node_name}>.")

                    if(output_field not in out_node_class.output_fields):
                        raise NameError(f"""Not existed field {output_field} in {out_node_class.Output} referenced by <node id={node_name}>.
                            The output fields of {out_node_class} are {out_node_class.output_fields}""")

                    out_type = out_node_class.output_fields[output_field].annotation
                    in_type = this_node.input_fields[input_field].annotation
                    if(out_type != in_type):
                        raise TypeError(f"""Type of output <node id={out_node}>.{output_field}({in_type}) is not the same as <node id={node_name}>.{in_var_name}({in_type})""")

                    self.graph.add_edge(out_node, node_name, output_field=output_field, input_field=input_field)

                    continue

                # Handle value
                if(node_name not in self.input_data):
                    self.input_data[node_name] = {}
                self.input_data[node_name][input_field] = deepcopy(data)

                if(node_name not in self.args_schema):
                    self.args_schema[node_name] = {}
                self.args_schema[node_name][input_field] = this_node.Input.__fields__[input_field]

    def _build_merkle_tree(self):
        in_degrees = self.graph.in_degree()

        # Handle leaf nodes
        leaf_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        for n in leaf_nodes:
            this_node = self.graph.nodes[n]

            # Hash of Leaf Nodes: hash(hash(Input); hash(Node))
            this_node['hash'] = stable_hash(
                    hash(this_node['node'].Input.parse_obj(self.input_data[n])),
                    hash(this_node['node'])).hexdigest()

        # Handle other nodes
        for n in nx.topological_sort(self.graph):  # nx.topological_sort will discard isolated nodes
            this_node = self.graph.nodes[n]
            if(in_degrees[n] == 0):
                continue
            elif(in_degrees[n] == len(this_node['node'].input_fields)):
                # Hash Nodes without ouside inputs: hash(hash(ParentNodes); hash(Node))
                this_node['hash'] = stable_hash(
                        list([self.graph.nodes(data=True)[anc_n]['hash'] for anc_n in sorted(nx.ancestors(self.graph, n))]),
                        hash(this_node['node'])).hexdigest()
            else:
                # Hash Nodes with ouside inputs: hash(hash(ParentNodes); hash(Input); hash(Node))
                this_node['hash'] = stable_hash(
                        list([self.graph.nodes(data=True)[anc_n]['hash'] for anc_n in sorted(nx.ancestors(self.graph, n))]),
                        self.input_data[n],
                        hash(this_node['node'])).hexdigest()

