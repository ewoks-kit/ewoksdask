"""
https://docs.dask.org/en/latest/scheduler-overview.html
"""

import json
import logging
from dask.distributed import Client
from dask.threaded import get as multithreading_scheduler
from dask.multiprocessing import get as multiprocessing_scheduler
from dask import get as sequential_scheduler

from ewokscore import load_graph
from ewokscore.inittask import instantiate_task
from ewokscore.inittask import add_dynamic_inputs
from ewokscore.graph import ewoks_jsonload_hook


logger = logging.getLogger(__name__)


def execute_task(execinfo, *inputs):
    execinfo = json.loads(execinfo, object_pairs_hook=ewoks_jsonload_hook)

    dynamic_inputs = dict()
    for source_results, link_attrs in zip(inputs, execinfo["link_attrs"]):
        add_dynamic_inputs(dynamic_inputs, link_attrs, source_results)
    task = instantiate_task(
        execinfo["node_attrs"],
        node_name=execinfo["node_name"],
        inputs=dynamic_inputs,
        varinfo=execinfo["varinfo"],
    )

    try:
        task.execute()
    except Exception as e:
        if execinfo["enable_logging"]:
            logger.error(
                "\nEXECUTE {} {}\n INPUTS: {}\n ERROR: {}".format(
                    execinfo["node_name"],
                    repr(task),
                    task.input_values,
                    e,
                ),
            )
        raise

    if execinfo["enable_logging"]:
        logger.info(
            "\nEXECUTE {} {}\n INPUTS: {}\n OUTPUTS: {}".format(
                execinfo["node_name"],
                repr(task),
                task.input_values,
                task.output_values,
            ),
        )

    return task.output_transfer_data


def convert_graph(ewoksgraph, varinfo, enable_logging=False):
    daskgraph = dict()
    for target, node_attrs in ewoksgraph.graph.nodes.items():
        sources = tuple(source for source in ewoksgraph.predecessors(target))
        link_attrs = tuple(ewoksgraph.graph[source][target] for source in sources)
        execinfo = {
            "node_name": target,
            "node_attrs": node_attrs,
            "link_attrs": link_attrs,
            "varinfo": varinfo,
            "enable_logging": enable_logging,
        }
        # Note: the execinfo is serialized to prevent dask
        #       from interpreting node names as task results
        daskgraph[target] = (execute_task, json.dumps(execinfo)) + sources
    return daskgraph


def execute_graph(
    graph,
    representation=None,
    varinfo=None,
    scheduler=None,
    log_task_execution=False,
    results_of_all_nodes=False,
    **load_options,
):
    ewoksgraph = load_graph(source=graph, representation=representation, **load_options)
    if ewoksgraph.is_cyclic:
        raise RuntimeError("Dask can only execute DAGs")
    if ewoksgraph.has_conditional_links:
        raise RuntimeError("Dask cannot handle conditional links")
    daskgraph = convert_graph(ewoksgraph, varinfo, enable_logging=log_task_execution)

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
