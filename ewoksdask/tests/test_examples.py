import sys
import logging
import pytest
import itertools
from ewoksdask import execute_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils import assert_taskgraph_result
from ewokscore.tests.utils import assert_workflow_result
from ewokscore import load_graph

logging.getLogger("dask").setLevel(logging.DEBUG)
logging.getLogger("dask").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("ewoksdask").setLevel(logging.DEBUG)
logging.getLogger("ewoksdask").addHandler(logging.StreamHandler(sys.stdout))


@pytest.mark.parametrize(
    "graph_name,scheduler,persist",
    itertools.product(
        graph_names(), (None, "multithreading", "multiprocessing"), (True, False)
    ),
)
def test_examples(graph_name, tmpdir, scheduler, persist):
    graph, expected = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    if persist:
        varinfo = {"root_uri": str(tmpdir)}
    else:
        varinfo = None
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            execute_graph(graph, scheduler=scheduler, varinfo=varinfo)
    else:
        result = execute_graph(
            graph, scheduler=scheduler, varinfo=varinfo, results_of_all_nodes=True
        )
        if persist:
            assert_taskgraph_result(ewoksgraph, expected, varinfo=varinfo)
        assert_workflow_result(result, expected, varinfo=varinfo)
