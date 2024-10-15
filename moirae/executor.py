from copy import deepcopy
import asyncio

import networkx as nx

from moirae import Graph, Latch


class Executor:
    def __init__(self, graph: Graph):
        assert isinstance(graph, Graph)

        self.graph = deepcopy(graph.graph)
        self.data = deepcopy(graph.data)
        self.outputs = asyncio.Queue()

    def _add_task(self):
        pass

    def _node_worker(self, node_instance):
        pass
