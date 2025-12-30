import pytest
from ewokscore.tests.test_workflow_events import assert_failed_workfow_events
from ewokscore.tests.test_workflow_events import assert_succesfull_workfow_events
from ewokscore.tests.test_workflow_events import fetch_events
from ewokscore.tests.test_workflow_events import run_failed_workfow
from ewokscore.tests.test_workflow_events import run_succesfull_workfow
from ewokscore.tests.test_workflow_events import sqlite_path  # noqa F401

from ewoksdask import execute_graph


@pytest.mark.parametrize("scheduler", (None, "multithreading", "multiprocessing"))
def test_succesfull_workfow(scheduler, sqlite_path):  # noqa F811
    database = sqlite_path / "ewoks_events.db"
    run_succesfull_workfow(database, execute_graph, scheduler=scheduler)
    events = fetch_events(database, 10)
    assert_succesfull_workfow_events(events)


@pytest.mark.parametrize("scheduler", (None, "multithreading", "multiprocessing"))
def test_failed_workfow(scheduler, sqlite_path):  # noqa F811
    database = sqlite_path / "ewoks_events.db"
    run_failed_workfow(database, execute_graph, scheduler=scheduler)
    events = fetch_events(database, 8)
    assert_failed_workfow_events(events)
