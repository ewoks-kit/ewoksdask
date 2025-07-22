Local execution
===============

Dask offers several `scheduler options <https://docs.dask.org/en/latest/scheduler-overview.html>`_
that allow workflow execution without requiring external services. These include:

- **Sequential**: Tasks are executed one after another, in a single thread.
- **Multi-threading**: Tasks are executed concurrently in multiple threads within the same process.
- **Multi-processing**: Tasks are executed concurrently in separate subprocesses of the current process.
- **Cluster**: A temporary Dask cluster is created for the duration of the workflow execution.

Example Workflow
-----------------

In the following example, we define a workflow with two independent nodes.
Since the nodes are not connected, they can execute in parallel:

.. code:: python

    from ewoksdask import execute_graph

    example_workflow = {
        "graph": {"id": "test"},
        "nodes": [
            {
                "id": "node1",
                "task_type": "method",
                "task_identifier": "time.sleep",
                "default_inputs": [{"name": 0, "value": 10}],
            },
            {
                "id": "node2",
                "task_type": "method",
                "task_identifier": "time.sleep",
                "default_inputs": [{"name": 0, "value": 10}],
            }
        ]
    }

    result = execute_graph(example_workflow, scheduler=..., scheduler_options=...)

You can choose different schedulers depending on your requirements:

Sequential
----------

Tasks are run one after another in a single thread.

.. code:: python

    result = execute_graph(example_workflow, scheduler=None)

Multi-Threading
---------------

Runs tasks in parallel using multiple threads.
This example completes in ~10 seconds using two threads:

.. code:: python

    result = execute_graph(
        workflow, scheduler="multithreading", scheduler_options={"num_workers": 2}
    )

Multi-Processing
----------------

Runs tasks in parallel using multiple subprocesses.
This example also completes in ~10 seconds using two processes:

.. code:: python

    if __name__ == "__main__":
        result = execute_graph(
            workflow,
            scheduler="multiprocessing",
            scheduler_options={"num_workers": 2, "context": "spawn"},
        )

.. note::

    The `if __name__ == "__main__":` guard is required when using the *spawn* context.

By default:

- On Linux, the default context is *fork*.

- On Windows/macOS, the default context is *spawn*.

See the `Python multiprocessing docs <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_ for details on contexts.

Cluster
-------

Creates a temporary local Dask cluster with the specified number of workers.
This example completes in ~10 seconds using two workers:

.. code:: python

    result = execute_graph(
        workflow, scheduler="cluster", scheduler_options={"n_workers": 2}
    )

Additional cluster configuration options are available in the
`Dask distributed.Client documentation <https://docs.dask.org/en/stable/futures.html?highlight=client#distributed.Client>`_.
