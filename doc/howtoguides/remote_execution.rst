Remote execution
================

Workflows can be executed on a *Dask cluster* started as an **external service**.

Below is an example of executing a workflow with two independent nodes.
Since the nodes are not connected, they can run in parallel:

.. code:: python

    from ewoksdask import execute_graph

    workflow = {
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
            },
        ],
    }

    result = execute_graph(workflow, scheduler="127.0.0.1:8786")

The scheduler parameter is the address of a *Dask scheduler*.

Local scheduler
---------------

You can start a local scheduler with multiple workers using the following command:

.. code:: bash

    ewoksdask local --n-workers 5 --threads-per-worker 10

This example launches:

- 5 worker processes

- Each with 10 threads

- Allowing up to 50 parallel tasks

.. code:: bash

    Address: tcp://127.0.0.1:8786
    Dashboard: http://127.0.0.1:8787/status
    Scheduler is running. Press CTRL-C to stop.

More configuration options can be found in the `Dask documentation <https://distributed.dask.org/en/latest/api.html#distributed.LocalCluster>`_.

The *dashboard* provides detailed real-time information about running jobs and worker activity.

Distributed scheduler
---------------------

To set up a distributed cluster, start the scheduler on a remote machine:

.. code:: bash

    dask scheduler

Example output:

.. code:: bash

    Scheduler at:  tcp://192.168.1.47:8786
    dashboard at:  http://192.168.1.47:8787/status

Next, connect workers to this scheduler. The example below adds 3 workers, each with
4 processes (totaling 12 concurrent tasks):

.. code:: bash

    dask worker 127.0.0.1:8786 --nprocs 4
    dask worker 127.0.0.1:8786 --nprocs 4
    dask worker 127.0.0.1:8786 --nprocs 4

Slurm scheduler
---------------

To use Dask with a Slurm-managed cluster, launch a scheduler from a *Slurm submitter node*
(i.e., a machine with Slurm client utilities configured):

.. code:: bash

    ewoksdask slurm --minimum-jobs 3 --maximum-jobs 10 --cores=2 --memory=64GB --walltime="01:00:00" --queue=gpu --gpus=1 --log debug

This command will:

- Launch 3 permanent jobs (restarted when terminated)
- Scale up to 10 jobs as needed
- Provide a maximum capacity of 10 concurrent tasks
- Each job will submitted to the *gpu* queue
- Each job will be terminated after one hour
- Each job will have the following resources for the execution of workflow tasks

  - 2 CPU cores
  - 1 GPU
  - 64GB of RAM

Refer to the Dask `JobQueue SlurmCluster documentation <https://jobqueue.dask.org/en/latest/generated/dask_jobqueue.SLURMCluster.html>`_
for more scheduler configuration options.
