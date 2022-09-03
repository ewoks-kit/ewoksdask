import pytest

from ewoksdask import execute_graph
from ewokscore import load_graph

from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils.results import assert_execute_graph_default_result


@pytest.mark.parametrize("graph_name", graph_names())
@pytest.mark.parametrize("scheduler", (None, "multithreading", "multiprocessing"))
@pytest.mark.parametrize("scheme", (None, "json"))
def test_examples(graph_name, tmpdir, scheduler, scheme):
    graph, expected = get_graph(graph_name)
    ewoksgraph = load_graph(graph)
    if scheme:
        varinfo = {"root_uri": str(tmpdir), "scheme": scheme}
    else:
        varinfo = None
    if ewoksgraph.is_cyclic or ewoksgraph.has_conditional_links:
        with pytest.raises(RuntimeError):
            execute_graph(graph, scheduler=scheduler, varinfo=varinfo)
    else:
        result = execute_graph(graph, scheduler=scheduler, varinfo=varinfo)
        assert_execute_graph_default_result(ewoksgraph, result, expected, varinfo)
