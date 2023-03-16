# Parallel execution

Scheduler options for parallel execution can be provided when executing a workflow

.. code:: python

    from ewoksdask import execute_graph

    result = execute_graph("/path/to/graph.json", scheduler=..., scheduler_options=...)

The different schedulers are

 * `multithreading`:
    * `num_workers`: CPU_COUNT by default
 * `multiprocessing`:
    * `context`: `spawn` or `fork`
    * `num_workers`: CPU_COUNT by default
 * `cluster`: scheduler with workers in the current process
    * `n_workers`: each worker has multiple threads
    * `threads_per_worker`:
    * `processes`: subprocesses instead of threads
 * `127.0.0.1:40331`: remote scheduler

## Remote scheduler

Start a scheduler (+ workers) on any host

.. code:: bash

    from ewoksdask.clusters import local_scheduler
    cluster = local_scheduler(n_workers=5)

### Separate processes

Start a scheduler on any host

.. code:: bash

    dask scheduler

Add workers to a scheduler with 4 cores each

.. code:: bash

    dask worker 127.0.0.1:8786 --nprocs 4
    dask worker 127.0.0.1:8786 --nprocs 4
    dask worker 127.0.0.1:8786 --nprocs 4

### Slurm scheduler

Start a scheduler on a Slurm submitter host (spawns one Slurm job for each worker)

.. code:: bash

    from ewoksdask.clusters import slurm_scheduler
    cluster = slurm_scheduler(maximum_jobs=5)
