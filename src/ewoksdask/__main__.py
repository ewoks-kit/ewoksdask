import argparse
import json
import logging
import sys
import time
from json.decoder import JSONDecodeError
from typing import Any
from typing import Dict
from typing import Tuple

from . import schedulers


def _parse_option(option: str) -> Tuple[str, Any]:
    option, _, value = option.partition("=")
    return option, _parse_value(value)


def _parse_value(value: str) -> Any:
    try:
        return json.loads(value)
    except JSONDecodeError:
        return value


_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start a Dask cluster (Local or SLURM)",
        prog="ewoksdask",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(help="Commands", dest="cluster_type")

    # Local cluster parser
    local_parser = subparsers.add_parser("local", help="Start a LocalCluster")
    local_parser.add_argument("--n-workers", type=int, default=1)
    local_parser.add_argument(
        "--no-processes",
        dest="processes",
        action="store_false",
        help="Disable multiprocessing",
    )
    local_parser.add_argument("--threads-per-worker", type=int)
    local_parser.add_argument("--scheduler-port", type=int)
    local_parser.add_argument("--dashboard-address", type=str, default=":8787")
    local_parser.add_argument("--worker-dashboard-address", type=str)
    local_parser.add_argument(
        "-o",
        "--option",
        dest="options",
        action="append",
        default=[],
        metavar="OPTION=VALUE",
        help="Other options: https://distributed.dask.org/en/latest/api.html#distributed.LocalCluster",
    )
    local_parser.add_argument(
        "-l",
        "--log",
        type=str.lower,
        choices=list(_LOG_LEVELS),
        default="info",
        help="Log level",
    )

    # SLURM cluster parser
    slurm_parser = subparsers.add_parser("slurm", help="Start a SLURMCluster")
    slurm_parser.add_argument("--n-workers", type=int)
    slurm_parser.add_argument("--minimum-jobs", type=int, default=0)
    slurm_parser.add_argument("--maximum-jobs", type=int, default=0)
    slurm_parser.add_argument("--queue", type=str, default=None)
    slurm_parser.add_argument("--cores", type=int, default=2)
    slurm_parser.add_argument("--gpus", type=int, default=None)
    slurm_parser.add_argument("--processes", type=int, default=1)
    slurm_parser.add_argument("--memory", type=str, default="1GB")
    slurm_parser.add_argument("--walltime", type=str, default="01:00:00")
    slurm_parser.add_argument(
        "-o",
        "--option",
        dest="options",
        action="append",
        default=[],
        metavar="OPTION=VALUE",
        help="Other options: https://jobqueue.dask.org/en/latest/generated/dask_jobqueue.SLURMCluster.html",
    )
    slurm_parser.add_argument(
        "-l",
        "--log",
        type=str.lower,
        choices=list(_LOG_LEVELS),
        default="info",
        help="Log level",
    )

    return parser


def _parse_scheduler_arguments(args) -> Dict[str, Any]:
    kwargs = vars(args)

    log_level = _LOG_LEVELS[kwargs.pop("log")]
    logging.basicConfig(level=log_level)

    options = dict(_parse_option(item) for item in kwargs.pop("options"))
    kwargs.update(options)

    cluster_type = kwargs.pop("cluster_type")
    return cluster_type, kwargs


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = _create_argument_parser()
    args = parser.parse_args(argv[1:])

    cluster_type, kwargs = _parse_scheduler_arguments(args)
    if cluster_type == "local":
        _ = schedulers.local_scheduler(**kwargs)
    elif cluster_type == "slurm":
        _ = schedulers.slurm_scheduler(**kwargs)

    try:
        print("Scheduler is running. Press CTRL-C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


if __name__ == "__main__":
    sys.exit(main())
