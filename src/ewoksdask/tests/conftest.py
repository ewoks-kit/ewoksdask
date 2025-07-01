import pytest

from ..engine import DaskWorkflowEngine


@pytest.fixture()
def engine():
    return DaskWorkflowEngine()
