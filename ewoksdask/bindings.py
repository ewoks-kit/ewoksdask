"""
https://docs.dask.org/en/latest/scheduler-overview.html
"""

import json
from typing import List, Optional, Union
from dask.distributed import Client
from dask.threaded import get as multithreading_scheduler
from dask.multiprocessing import get as multiprocessing_scheduler
from dask import get as sequential_scheduler

from ewokscore import load_graph
from ewokscore import execute_graph_decorator
from ewokscore.inittask import instantiate_task
from ewokscore.inittask import add_dynamic_inputs
from ewokscore.graph.serialize import ewoks_jsonload_hook
from ewokscore.node import get_node_label
from ewokscore.graph import analysis
from ewokscore import events


def execute_task(execute_options, *inputs):
    execute_options = json.loads(execute_options, object_pairs_hook=ewoks_jsonload_hook)

    dynamic_inputs = dict()
    for source_results, link_attrs in zip(inputs, execute_options["link_attrs"]):
        add_dynamic_inputs(dynamic_inputs, link_attrs, source_results)
    task = instantiate_task(
        execute_options["node_id"],
        execute_options["node_attrs"],
        inputs=dynamic_inputs,
        varinfo=execute_options.get("varinfo"),
        execinfo=execute_options.get("execinfo"),
    )

    task.execute()

    return task.output_transfer_data


def convert_graph(ewoksgraph, **execute_options):
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
        # Note: the execute_options is serialized to prevent dask
        #       from interpreting node names as task results
        daskgraph[target_id] = (execute_task, json.dumps(execute_options)) + source_ids
    return daskgraph


def execute_dask_graph(
    daskgraph,
    nodes: List[str],
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
):
    if scheduler_options is None:
        scheduler_options = dict()
    if scheduler is None:
        results = sequential_scheduler(daskgraph, nodes, **scheduler_options)
    elif scheduler == "multiprocessing":
        # num_workers: CPU_COUNT by default
        results = multiprocessing_scheduler(daskgraph, nodes, **scheduler_options)
    elif scheduler == "multithreading":
        # num_workers: CPU_COUNT by default
        results = multithreading_scheduler(daskgraph, nodes, **scheduler_options)
    elif scheduler == "cluster":
        # n_worker: n worker with m threads (n_worker= n * m)
        with Client(**scheduler_options) as client:
            results = client.get(daskgraph, nodes)
    elif isinstance(scheduler, str):
        with Client(address=scheduler, **scheduler_options) as client:
            results = client.get(daskgraph, nodes)
    elif isinstance(scheduler, Client):
        results = client.get(daskgraph, nodes)
    else:
        raise ValueError("Unknown scheduler")

    return dict(zip(nodes, results))


def _execute_graph(
    ewoksgraph,
    results_of_all_nodes: Optional[bool] = False,
    outputs: Optional[List[dict]] = None,
    varinfo: Optional[dict] = None,
    execinfo: Optional[dict] = None,
    scheduler: Union[dict, str, None, Client] = None,
    scheduler_options: Optional[dict] = None,
):
    with events.workflow_context(execinfo, workflow=ewoksgraph.graph) as execinfo:
        if ewoksgraph.is_cyclic:
            raise RuntimeError("Dask can only execute DAGs")
        if ewoksgraph.has_conditional_links:
            raise RuntimeError("Dask cannot handle conditional links")

        daskgraph = convert_graph(ewoksgraph, varinfo=varinfo, execinfo=execinfo)
        if results_of_all_nodes:
            nodes = list(ewoksgraph.graph.nodes)
        else:
            nodes = list(analysis.end_nodes(ewoksgraph.graph))
        return execute_dask_graph(
            daskgraph, nodes, scheduler=scheduler, scheduler_options=scheduler_options
        )


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
