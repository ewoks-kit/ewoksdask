# https://docs.dask.org/en/latest/scheduler-overview.html

import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import dask
from dask import get as sequential_scheduler
from dask.delayed import Delayed
from dask.distributed import Client
from dask.distributed import wait
from dask.distributed.client import Future
from dask.multiprocessing import get as multiprocessing_scheduler
from dask.threaded import get as multithreading_scheduler
from ewokscore import events
from ewokscore import execute_graph_decorator
from ewokscore import load_graph
from ewokscore.graph import TaskGraph
from ewokscore.graph import analysis
from ewokscore.graph import graph_io
from ewokscore.graph.serialize import json_load
from ewokscore.inittask import add_dynamic_inputs
from ewokscore.inittask import instantiate_task
from ewokscore.node import NodeIdType
from ewokscore.node import get_node_label


def _execute_task(serialized_opts, *all_source_results: dict) -> dict:
    execute_options = json_load(serialized_opts)

    dynamic_inputs = dict()
    target_id = execute_options["node_id"]
    for source_id, source_results, link_attrs in zip(
        execute_options["source_ids"], all_source_results, execute_options["link_attrs"]
    ):
        add_dynamic_inputs(
            dynamic_inputs,
            link_attrs,
            source_results,
            source_id=source_id,
            target_id=target_id,
        )
    task = instantiate_task(
        execute_options["node_id"],
        execute_options["node_attrs"],
        inputs=dynamic_inputs,
        varinfo=execute_options.get("varinfo"),
        execinfo=execute_options.get("execinfo"),
        task_options=execute_options.get("task_options"),
    )

    task.execute()

    return task.get_output_transfer_data()


def _create_dask_graph(ewoksgraph, **execute_options) -> dict:
    daskgraph = dict()
    for target_id, node_attrs in ewoksgraph.graph.nodes.items():
        source_ids = tuple(analysis.node_predecessors(ewoksgraph.graph, target_id))
        link_attrs = tuple(
            ewoksgraph.graph[source_id][target_id] for source_id in source_ids
        )
        node_label = get_node_label(target_id, node_attrs)

        node_execute_options = dict(execute_options)
        node_execute_options["node_id"] = target_id
        node_execute_options["node_label"] = node_label
        node_execute_options["node_attrs"] = node_attrs
        node_execute_options["link_attrs"] = link_attrs
        node_execute_options["source_ids"] = source_ids

        # Note: the execute options are serialized to prevent dask
        #       from interpreting node names as task results
        daskgraph[target_id] = (
            _execute_task,
            json.dumps(node_execute_options),
        ) + source_ids
    return daskgraph


def _execute_dask_graph(
    daskgraph: dict,
    node_ids: List[NodeIdType],
    output_node_ids: List[NodeIdType],
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
) -> Dict[NodeIdType, Any]:
    if scheduler_options is None:
        scheduler_options = dict()

    if scheduler is None:
        results = sequential_scheduler(daskgraph, node_ids, **scheduler_options)
        return dict(zip(node_ids, results))

    if scheduler == "multiprocessing":
        # num_workers: CPU_COUNT by default
        scheduler_options = dict(scheduler_options)
        context = scheduler_options.pop("context", "spawn")
        dask.config.set({"multiprocessing.context": context})
        results = multiprocessing_scheduler(daskgraph, node_ids, **scheduler_options)
        return dict(zip(node_ids, results))

    if scheduler == "multithreading":
        # num_workers: CPU_COUNT by default
        results = multithreading_scheduler(daskgraph, node_ids, **scheduler_options)
        return dict(zip(node_ids, results))

    if scheduler == "cluster":
        # n_workers: n workers with m threads
        with Client(**scheduler_options) as client:
            return _submit_with_client(client, daskgraph, node_ids, output_node_ids)

    if isinstance(scheduler, str):
        with Client(address=scheduler, **scheduler_options) as client:
            return _submit_with_client(client, daskgraph, node_ids, output_node_ids)

    if isinstance(scheduler, Client):
        return _submit_with_client(client, daskgraph, node_ids, output_node_ids)

    raise ValueError("Unknown scheduler")


def _submit_with_client(
    client: Client,
    daskgraph,
    node_ids: List[NodeIdType],
    output_node_ids: List[NodeIdType],
    has_resource_specifiers: bool = True,
) -> Dict[NodeIdType, Any]:
    if node_ids == output_node_ids and not has_resource_specifiers:
        results = client.get(daskgraph, node_ids)
        return dict(zip(node_ids, results))

    futures: Dict[NodeIdType, Future] = {}
    delayed: Dict[NodeIdType, Delayed] = {}
    for node_id in node_ids:
        task_tuple = daskgraph[node_id]
        func, serialized_opts, *source_ids = task_tuple

        # TODO: pass Delayed or Future instances to the new Delayed function?
        delayed_results: List[Delayed] = [
            delayed[source_id] for source_id in source_ids
        ]
        args = [serialized_opts] + delayed_results
        delayed_task = dask.delayed(func)(*args)
        delayed[node_id] = delayed_task

        # TODO: resources are like task inputs:
        #   - defaults in the node attrs
        #   - can be overwritten when executing
        node_attrs = json.loads(serialized_opts)["node_attrs"]
        resources = node_attrs.get("resources", None)

        future = client.compute(delayed_task, resources=resources)
        futures[node_id] = future

    all_futures = list(futures.values())
    result_futures = [
        future for node_id, future in futures.items() if node_id in output_node_ids
    ]
    results = client.gather(result_futures)
    wait(all_futures)
    return dict(zip(output_node_ids, results))


def _execute_graph(
    ewoksgraph: TaskGraph,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    task_options: Optional[dict] = None,
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
) -> Dict[NodeIdType, Any]:
    with events.workflow_context(execinfo, workflow=ewoksgraph.graph) as execinfo:
        if ewoksgraph.is_cyclic:
            raise RuntimeError("Dask can only execute DAGs")
        if ewoksgraph.has_conditional_links:
            raise RuntimeError("Dask cannot handle conditional links")

        daskgraph = _create_dask_graph(
            ewoksgraph,
            varinfo=varinfo,
            execinfo=execinfo,
            task_options=task_options,
        )
        outputs = graph_io.parse_outputs(ewoksgraph.graph, outputs)
        output_node_ids = [output_item["id"] for output_item in outputs]
        node_ids = list(analysis.topological_sort(ewoksgraph.graph))

        result = _execute_dask_graph(
            daskgraph,
            node_ids,
            output_node_ids,
            scheduler=scheduler,
            scheduler_options=scheduler_options,
        )
        output_values = dict()
        for node_id, task_outputs in result.items():
            graph_io.add_output_values(
                output_values,
                node_id,
                task_outputs,
                outputs,
                merge_outputs=merge_outputs,
            )
        return output_values


@execute_graph_decorator(engine="dask")
def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    task_options: Optional[dict] = None,
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
) -> Dict[NodeIdType, Any]:
    if load_options is None:
        load_options = dict()
    ewoksgraph = load_graph(graph, inputs=inputs, **load_options)
    return _execute_graph(
        ewoksgraph,
        outputs=outputs,
        merge_outputs=merge_outputs,
        varinfo=varinfo,
        execinfo=execinfo,
        task_options=task_options,
        scheduler=scheduler,
        scheduler_options=scheduler_options,
    )
