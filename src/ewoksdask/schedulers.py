"""Schedulers with an address and status dashboard."""

from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster


def local_scheduler(**kw):
    """
    :param n_workers:
    :param processes: True by default
    :param threads_per_worker:
    :param scheduler_port:
    :param dashboard_address:
    :param worker_dashboard_address:
    """
    kw.setdefault("n_workers", 1)

    cluster = LocalCluster(**kw)

    print("Address:", cluster.scheduler_address)
    print("Dashboard:", cluster.dashboard_link)
    return cluster


def slurm_scheduler(**kw):
    """
    :param address:
    :param n_workers:
    :param minimum_jobs:
    :param maximum_jobs:
    :param cores:
    :param processes:
    :param gpus:
    :param memory:
    :param queue:
    """
    kw.setdefault("walltime", "01:00:00")
    kw.setdefault("cores", 2)
    kw.setdefault("processes", 1)
    kw.setdefault("memory", "8GB")
    job_extra_directives = kw.setdefault("job_extra_directives", list())

    minimum_jobs = kw.pop("minimum_jobs", 0)
    maximum_jobs = kw.pop("maximum_jobs", 0)
    kw.setdefault("n_workers", int(not maximum_jobs))

    gpus = kw.pop("gpus", 0)
    if gpus:
        job_extra_directives.append(f"--gres=gpu:{gpus}")

    cluster = SLURMCluster(**kw)
    if maximum_jobs:
        cluster.adapt(minimum_jobs=minimum_jobs, maximum_jobs=maximum_jobs)

    print("Address:", cluster.scheduler_address)
    print("Dashboard:", cluster.dashboard_link)
    return cluster
