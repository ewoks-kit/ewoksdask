import sys
import logging
import pytest
from ewoksdask import execute_graph
from ewokscore.tests.examples import graphs
from ewokscore.tests.utils import assert_taskgraph_result

logging.getLogger("dask").setLevel(logging.DEBUG)
logging.getLogger("dask").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("ewoksdask").setLevel(logging.DEBUG)
logging.getLogger("ewoksdask").addHandler(logging.StreamHandler(sys.stdout))


@pytest.mark.parametrize("scheduler", [None, "multithreading", "multiprocessing"])
def test_execute_graph(tmpdir, scheduler):
    varinfo = {"root_uri": str(tmpdir)}
    graph, expected = graphs.acyclic_graph1()
    execute_graph(graph, varinfo=varinfo, scheduler=scheduler)
    assert_taskgraph_result(graph, expected, varinfo)
