"""
https://docs.dask.org/en/latest/scheduler-overview.html
"""

from dask.distributed import Client
from dask.threaded import get as multithreading_scheduler
from dask.multiprocessing import get as multiprocessing_scheduler
from dask import get as sequential_scheduler

from ewokscore import load_graph


def execute_task(node_name, *inputs):
    node_name = node_name[:-3]
    info = inputs[0]
    esrfgraph = load_graph(info["esrfgraph"])
    task = esrfgraph.instantiate_task_static(node_name, varinfo=info["varinfo"])
    task.execute()
    return info


def convert_graph(esrfgraph, varinfo):
    daskgraph = dict()
    for target in esrfgraph.graph.nodes:
        sources = tuple(source for source in esrfgraph.predecessors(target))
        if not sources:
            sources = ({"esrfgraph": esrfgraph, "varinfo": varinfo},)
        partial = (execute_task, target + "...")
        daskgraph[target] = partial + sources
    return daskgraph


def job(graph, representation=None, varinfo=None, scheduler=None):
    esrfgraph = load_graph(source=graph, representation=representation)
    if esrfgraph.is_cyclic:
        raise RuntimeError("Dask can only execute DAGs")
    if esrfgraph.has_conditional_links:
        raise RuntimeError("Dask cannot handle conditional links")
    daskgraph = convert_graph(esrfgraph, varinfo)

    nodes = list()
    for node in esrfgraph.graph.nodes:
        if len(list(esrfgraph.graph.successors(node))) == 0:
            nodes.append(node)

    if scheduler is None:
        sequential_scheduler(daskgraph, nodes)
    elif isinstance(scheduler, str):
        if scheduler == "multiprocessing":
            multiprocessing_scheduler(daskgraph, nodes)
        elif scheduler == "multithreading":
            multithreading_scheduler(daskgraph, nodes)
        else:
            raise ValueError("Unknown scheduler")
    elif isinstance(scheduler, dict):
        with Client(**scheduler) as scheduler:
            scheduler.get(daskgraph, nodes)
    else:
        scheduler.get(daskgraph, nodes)
