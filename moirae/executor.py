from copy import deepcopy
import asyncio

import networkx as nx

from moirae import Graph, Latch, Node


class Executor:
    def __init__(self, graph: Graph):
        assert isinstance(graph, Graph)

        self.graph = deepcopy(graph.graph)
        self.data_lock = asyncio.Lock()
        self.input_data = deepcopy(graph.input_data)
        self.outputs = asyncio.Queue()

        self.done = False

        self.tasks = self._dispatch_tasks()
        asyncio.create_task(self.execute())

    def __aiter__(self):
        return self

    async def __anext__(self):
        result = await self.outputs.get()

        if self.done:
            raise StopAsyncIteration

        return result

    async def execute(self):
        exc = None
        for coro in asyncio.as_completed(self.tasks):
            try:
                await coro
            except Exception as e:
                exc = e
                break

        # Send a stop signal
        self.done = True
        await self.outputs.put(None)

        if(exc):
            for t in self.tasks:
                if(not t.done()):
                    t.cancel()

            raise exc

    def _dispatch_tasks(self):
        # Plan latch
        for node_name in self.graph.nodes:
            predcessors = set(self.graph.predecessors(node_name))
            latch = Latch(len(predcessors))

            self.graph.nodes(data=True)[node_name]['latch'] = latch
            # Add hook to predcessors for counting down
            for p in predcessors:
                if(not hasattr(self.graph.nodes(data=True)[p], 'latch_to_countdown')):
                    self.graph.nodes(data=True)[p]['latch_to_countdown'] = []
                self.graph.nodes(data=True)[p]['latch_to_countdown'].append(latch)

        # Plan dataflow
        dataflows = {}
        for out_node, in_node, out_edge in self.graph.out_edges(data=True):
            if(out_node not in dataflows):
                dataflows[out_node] = {}
            if(in_node not in dataflows[out_node]):
                dataflows[out_node][in_node] = []

            dataflows[out_node][in_node].append((out_edge['output_field'], out_edge['input_field']))
        for out_node, in_nodes in dataflows.items():
            self.graph.nodes(data=True)[out_node]['dataflow'] = in_nodes

        # Create coroutines
        coroutines = []
        for node_name, node_data in self.graph.nodes(data=True):
            coroutines.append(
                asyncio.create_task(
                    self._node_worker(node_name,
                        node_data['node'],
                        node_data['dataflow'] if 'dataflow' in node_data else {},
                        node_data['latch'],
                        node_data['latch_to_countdown'] if 'latch_to_countdown' in node_data else [])))

        return coroutines

    async def _node_worker(self,
        node_name: str,
        node: Node,
        dataflow: dict[str, list[tuple[str, str]]],  # {"out_node": [("output_field", "input_field")]}
        upstream_latch: Latch,
        downstream_latch: list[Latch]):
        await upstream_latch.wait()

        try:
            # Parse data
            data = node.Input.parse_obj(self.input_data[node_name])

            # Execute the node
            node.check_inputs(data)
            outputs = await node.execute(data)
            node.check_outputs(outputs)

            # Dispatch data
            async with self.data_lock:
                for out_node, data_flow in dataflow.items():
                    for output_field, input_field in data_flow:
                        if(out_node not in self.input_data):
                            self.input_data[out_node] = {}
                        if(input_field not in self.input_data[out_node]):
                            self.input_data[out_node][input_field] = {}

                        data = getattr(outputs, output_field)
                        self.input_data[out_node][input_field] = deepcopy(data)

            for l in downstream_latch:
                await l.count_down()

            # Return data
            self.outputs.put_nowait((node_name, deepcopy(outputs)))
        except Exception as e:
            raise RuntimeError(f"Error while handling node <{node_name}>") from e
