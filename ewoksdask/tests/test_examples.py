import pytest

from ewoksdask import execute_graph
from ewokscore import load_graph

from ewokscore.tests.examples.graphs import graph_names
from ewokscore.tests.examples.graphs import get_graph
from ewokscore.tests.utils.results import assert_execute_graph_all_tasks
from ewokscore.tests.utils.results import assert_execute_graph_tasks
from ewokscore.tests.utils.results import filter_expected_results


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
        return

    result = execute_graph(
        graph, scheduler=scheduler, varinfo=varinfo, results_of_all_nodes=True
    )
    assert_all_results(ewoksgraph, result, expected, varinfo)
    result = execute_graph(
        graph, scheduler=scheduler, varinfo=varinfo, results_of_all_nodes=False
    )
    assert_end_results(ewoksgraph, result, expected, varinfo)


def assert_all_results(ewoksgraph, result, expected, varinfo):
    if varinfo:
        scheme = varinfo.get("scheme")
    else:
        scheme = None
    if scheme:
        assert_execute_graph_all_tasks(ewoksgraph, expected, varinfo=varinfo)
    assert_execute_graph_tasks(result, expected, varinfo=varinfo)


def assert_end_results(ewoksgraph, result, expected, varinfo):
    expected = filter_expected_results(ewoksgraph, expected, end_only=True)
    assert_execute_graph_tasks(result, expected, varinfo=varinfo)
