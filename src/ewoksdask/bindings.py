# https://docs.dask.org/en/latest/scheduler-overview.html

import json
from typing import Any, Dict, List, Optional, Union

import dask
from dask.distributed import Client
from dask.threaded import get as multithreading_scheduler
from dask.multiprocessing import get as multiprocessing_scheduler
from dask import get as sequential_scheduler

from ewokscore import load_graph
from ewokscore import execute_graph_decorator
from ewokscore.inittask import instantiate_task
from ewokscore.inittask import add_dynamic_inputs
from ewokscore.graph.serialize import ewoks_jsonload_hook
from ewokscore.node import NodeIdType
from ewokscore.node import get_node_label
from ewokscore.graph import analysis
from ewokscore.graph import graph_io
from ewokscore.graph import TaskGraph
from ewokscore import events


def _execute_task(execute_options, *inputs):
    execute_options = json.loads(execute_options, object_pairs_hook=ewoks_jsonload_hook)

    dynamic_inputs = dict()
    target_id = execute_options["node_id"]
    for source_id, source_results, link_attrs in zip(
        execute_options["source_ids"], inputs, execute_options["link_attrs"]
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
    )

    task.execute()

    return task.output_transfer_data


def _create_dask_graph(ewoksgraph, **execute_options) -> dict:
    daskgraph = dict()
    for target_id, node_attrs in ewoksgraph.graph.nodes.items():
        source_ids = tuple(analysis.node_predecessors(ewoksgraph.graph, target_id))
        link_attrs = tuple(
            ewoksgraph.graph[source_id][target_id] for source_id in source_ids
        )
        node_label = get_node_label(target_id, node_attrs)
        execute_options["node_id"] = target_id
        execute_options["node_label"] = node_label
        execute_options["node_attrs"] = node_attrs
        execute_options["link_attrs"] = link_attrs
        execute_options["source_ids"] = source_ids
        # Note: the execute_options is serialized to prevent dask
        #       from interpreting node names as task results
        daskgraph[target_id] = (_execute_task, json.dumps(execute_options)) + source_ids
    return daskgraph


def _execute_dask_graph(
    daskgraph,
    node_ids: List[NodeIdType],
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
) -> Dict[NodeIdType, Any]:
    if scheduler_options is None:
        scheduler_options = dict()
    if scheduler is None:
        results = sequential_scheduler(daskgraph, node_ids, **scheduler_options)
    elif scheduler == "multiprocessing":
        # num_workers: CPU_COUNT by default
        scheduler_options = dict(scheduler_options)
        context = scheduler_options.pop("context", "spawn")
        dask.config.set({"multiprocessing.context": context})
        results = multiprocessing_scheduler(daskgraph, node_ids, **scheduler_options)
    elif scheduler == "multithreading":
        # num_workers: CPU_COUNT by default
        results = multithreading_scheduler(daskgraph, node_ids, **scheduler_options)
    elif scheduler == "cluster":
        # n_worker: n worker with m threads (n_worker= n * m)
        with Client(**scheduler_options) as client:
            results = client.get(daskgraph, node_ids)
    elif isinstance(scheduler, str):
        with Client(address=scheduler, **scheduler_options) as client:
            results = client.get(daskgraph, node_ids)
    elif isinstance(scheduler, Client):
        results = client.get(daskgraph, node_ids)
    else:
        raise ValueError("Unknown scheduler")

    return dict(zip(node_ids, results))


def _execute_graph(
    ewoksgraph: TaskGraph,
    outputs: Optional[List[dict]] = None,
    merge_outputs: Optional[bool] = True,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
) -> Dict[NodeIdType, Any]:
    with events.workflow_context(execinfo, workflow=ewoksgraph.graph) as execinfo:
        if ewoksgraph.is_cyclic:
            raise RuntimeError("Dask can only execute DAGs")
        if ewoksgraph.has_conditional_links:
            raise RuntimeError("Dask cannot handle conditional links")

        daskgraph = _create_dask_graph(ewoksgraph, varinfo=varinfo, execinfo=execinfo)
        outputs = graph_io.parse_outputs(ewoksgraph.graph, outputs)
        node_ids = list(analysis.topological_sort(ewoksgraph.graph))

        result = _execute_dask_graph(
            daskgraph,
            node_ids,
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


@execute_graph_decorator(binding="dask")
def execute_graph(
    graph,
    inputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    ewoksgraph = load_graph(graph, inputs=inputs, **load_options)
    return _execute_graph(ewoksgraph, **execute_options)
