import sys
import logging
import pytest
import itertools
from ewoksdask import execute_graph
from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils import assert_taskgraph_result
from ewokscore import load_graph

logging.getLogger("dask").setLevel(logging.DEBUG)
logging.getLogger("dask").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("ewoksdask").setLevel(logging.DEBUG)
logging.getLogger("ewoksdask").addHandler(logging.StreamHandler(sys.stdout))


@pytest.mark.parametrize(
    "graph_name,scheduler",
    itertools.product(graph_names(), (None, "multithreading", "multiprocessing")),
)
def test_examples(graph_name, tmpdir, scheduler):
    graph, expected = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    varinfo = {"root_uri": str(tmpdir)}
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            execute_graph(graph, varinfo=varinfo)
    else:
        execute_graph(graph, varinfo=varinfo)
        assert_taskgraph_result(ewoksgraph, expected, varinfo=varinfo)
