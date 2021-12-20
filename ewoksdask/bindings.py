"""
https://docs.dask.org/en/latest/scheduler-overview.html
"""

import json
from typing import List, Optional
from dask.distributed import Client
from dask.threaded import get as multithreading_scheduler
from dask.multiprocessing import get as multiprocessing_scheduler
from dask import get as sequential_scheduler

from ewokscore import load_graph
from ewokscore.inittask import instantiate_task
from ewokscore.inittask import add_dynamic_inputs
from ewokscore.graph import ewoks_jsonload_hook
from ewokscore.node import get_node_label


def execute_task(execinfo, *inputs):
    execinfo = json.loads(execinfo, object_pairs_hook=ewoks_jsonload_hook)

    dynamic_inputs = dict()
    for source_results, link_attrs in zip(inputs, execinfo["link_attrs"]):
        add_dynamic_inputs(dynamic_inputs, link_attrs, source_results)
    task = instantiate_task(
        execinfo["node_attrs"],
        node_id=execinfo["node_id"],
        inputs=dynamic_inputs,
        varinfo=execinfo["varinfo"],
    )

    task.execute()

    return task.output_transfer_data


def convert_graph(ewoksgraph, **execute_options):
    daskgraph = dict()
    for target_id, node_attrs in ewoksgraph.graph.nodes.items():
        source_ids = tuple(ewoksgraph.predecessors(target_id))
        link_attrs = tuple(
            ewoksgraph.graph[source_id][target_id] for source_id in source_ids
        )
        node_label = get_node_label(node_attrs, node_id=target_id)
        execute_options["node_id"] = target_id
        execute_options["node_label"] = node_label
        execute_options["node_attrs"] = node_attrs
        execute_options["link_attrs"] = link_attrs
        # Note: the execute_options is serialized to prevent dask
        #       from interpreting node names as task results
        daskgraph[target_id] = (execute_task, json.dumps(execute_options)) + source_ids
    return daskgraph


def execute_graph(
    graph,
    scheduler=None,
    inputs: Optional[List[dict]] = None,
    results_of_all_nodes: Optional[bool] = False,
    outputs: Optional[List[dict]] = None,
    load_options: Optional[dict] = None,
    **execute_options
):
    if load_options is None:
        load_options = dict()
    ewoksgraph = load_graph(source=graph, **load_options)
    if ewoksgraph.is_cyclic:
        raise RuntimeError("Dask can only execute DAGs")
    if ewoksgraph.has_conditional_links:
        raise RuntimeError("Dask cannot handle conditional links")
    if inputs:
        ewoksgraph.update_default_inputs(inputs)
    daskgraph = convert_graph(ewoksgraph, **execute_options)

    if results_of_all_nodes:
        nodes = list(ewoksgraph.graph.nodes)
    else:
        nodes = list(ewoksgraph.end_nodes())

    if scheduler is None:
        results = sequential_scheduler(daskgraph, nodes)
    elif isinstance(scheduler, str):
        if scheduler == "multiprocessing":
            results = multiprocessing_scheduler(daskgraph, nodes)
        elif scheduler == "multithreading":
            results = multithreading_scheduler(daskgraph, nodes)
        else:
            raise ValueError("Unknown scheduler")
    elif isinstance(scheduler, dict):
        with Client(**scheduler) as scheduler:
            results = scheduler.get(daskgraph, nodes)
    else:
        results = scheduler.get(daskgraph, nodes)

    return dict(zip(nodes, results))
