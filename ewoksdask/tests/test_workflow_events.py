import pytest
from ewoksdask import execute_graph
from ewokscore.tests.test_workflow_events import fetch_events
from ewokscore.tests.test_workflow_events import run_succesfull_workfow
from ewokscore.tests.test_workflow_events import run_failed_workfow
from ewokscore.tests.test_workflow_events import assert_succesfull_workfow_events
from ewokscore.tests.test_workflow_events import assert_failed_workfow_events


@pytest.mark.parametrize("scheduler", (None, "multithreading", "multiprocessing"))
def test_succesfull_workfow(scheduler, tmpdir):
    uri = run_succesfull_workfow(tmpdir, execute_graph, scheduler=scheduler)
    events = fetch_events(uri, 10)
    assert_succesfull_workfow_events(events)


@pytest.mark.parametrize("scheduler", (None, "multithreading", "multiprocessing"))
def test_failed_workfow(scheduler, tmpdir):
    uri = run_failed_workfow(tmpdir, execute_graph, scheduler=scheduler)
    events = fetch_events(uri, 8)
    assert_failed_workfow_events(events)
