from copy import deepcopy
import asyncio
from warnings import warn
import networkx as nx

from moirae.latch import Latch
from moirae.serialize import serialize, deserialize
from moirae import Graph, Node, Data, Cache, CacheIOError


class Executor:
    def __init__(self, graph: Graph, cache: Cache = None):
        assert isinstance(graph, Graph)

        self.graph = deepcopy(graph.graph)
        self.input_data = deepcopy(graph.input_data)
        self.outputs = asyncio.Queue()

        self.done = False
        self.cache = cache

        # Execute
        asyncio.create_task(self.execute())

    def __aiter__(self):
        return self

    async def __anext__(self):
        result = await self.outputs.get()

        if self.done:
            raise StopAsyncIteration

        return result

    def _plan_latch(self):
        for node_name in self.graph.nodes:
            predcessors = set(self.graph.predecessors(node_name))
            latch = Latch(len(predcessors))

            self.graph.nodes(data=True)[node_name]['latch'] = latch
            # Add hook to predcessors for counting down
            for p in predcessors:
                if(not hasattr(self.graph.nodes(data=True)[p], 'latch_to_countdown')):
                    self.graph.nodes(data=True)[p]['latch_to_countdown'] = []
                self.graph.nodes(data=True)[p]['latch_to_countdown'].append(latch)

    def _plan_dataflow(self):
        dataflows = {}
        for out_node, in_node, out_edge in self.graph.out_edges(data=True):
            if(out_node not in dataflows):
                dataflows[out_node] = {}
            if(in_node not in dataflows[out_node]):
                dataflows[out_node][in_node] = []

            dataflows[out_node][in_node].append((out_edge['output_field'], out_edge['input_field']))

        for out_node, in_nodes in dataflows.items():
            self.graph.nodes(data=True)[out_node]['dataflow'] = in_nodes

    def _dispatch_tasks(self):
        self._plan_latch()
        self._plan_dataflow()

        # Create coroutines
        coroutines = []
        for node_name, node_data in self.graph.nodes(data=True):
            coroutines.append(
                asyncio.create_task(
                    self._node_worker(node_name,
                        node_data['node'],
                        node_data['dataflow'] if 'dataflow' in node_data else {},
                        node_data['latch'],
                        node_data['latch_to_countdown'] if 'latch_to_countdown' in node_data else [],
                        node_data['hash'])))

        return coroutines

    async def _check_cache(self):
        hashes = {n[1]['hash'] for n in self.graph.nodes(data=True)}

        async def check_cache_wrapper(hash_val: str):
            try:
                return await self.cache.exists(hash_val)
            except Exception as e:
                warn(f"Error checking cache for hash {hash_val}，exception {e}", stacklevel=2)

                return False

        return {h for h, is_valid in zip(hashes, await asyncio.gather(*map(check_cache_wrapper, hashes)))
            if is_valid}

    async def execute(self):
        if(self.cache):
            self.available_cache = await self._check_cache()

        self.tasks = self._dispatch_tasks()

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

    async def _node_worker(self,
        node_name: str,
        node: Node,
        dataflow: dict[str, list[tuple[str, str]]],  # {"out_node": [("output_field", "input_field")]}
        upstream_latch: Latch,
        downstream_latch: list[Latch],
        hash_val: str):
        await upstream_latch.wait()

        try:
            if(self.cache and hash_val in self.available_cache):
                try:
                    # Cache hit
                    outputs = node.Output.parse_obj(deserialize(await self.cache.get(hash_val)))
                except Exception as e:
                    # Always execute if cannot get cache
                    outputs = await self._execute_node(node_name, node)
                    warn(f"Error getting cache while handling node <{node_name}>，exception {e}", stacklevel=2)
            else:
                # Cache miss, execute node
                outputs = await self._execute_node(node_name, node)

            # Dispatch data to downstream nodes
            self._dispatch_data(outputs, dataflow)

            for l in downstream_latch:
                await l.count_down()

            # Return data
            self.outputs.put_nowait((node_name, deepcopy(outputs)))

            # Put cache
            if(self.cache):
                try:
                    await self.cache.put(hash_val, serialize(dict(outputs)))
                except Exception as e:
                    warn(f"Error putting cache while handling node <{node_name}>，exception {e}", stacklevel=2)
        except Exception as e:
            # self.outputs.put_nowait((node_name, e))
            raise RuntimeError(f"Error while handling node <{node_name}>") from e

    async def _execute_node(self, node_name: str, node: Node):
        # Parse data
        data = node.Input.parse_obj(self.input_data.pop(node_name))

        # Execute the node
        node.check_inputs(data)
        outputs = await node.execute(data)
        node.check_outputs(outputs)

        return outputs

    def _dispatch_data(self,
        node_outputs: Data,
        dataflow: dict[str, list[tuple[str, str]]]):
        for out_node, data_flow in dataflow.items():
            for output_field, input_field in data_flow:
                data = getattr(node_outputs, output_field)
                self.input_data[out_node][input_field] = deepcopy(data)


execute_async = Executor


def execute(*args, **kwargs):
    async def execute_wrapper():
        return {node_name: node_output async for (node_name, node_output) in Executor(*args, **kwargs)}

    return asyncio.run(execute_wrapper())
