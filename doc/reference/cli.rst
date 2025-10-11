CLI reference
=============

ewoksdask local
---------------

.. argparse::
    :module: ewoksdask.__main__
    :func: _create_argument_parser
    :prog: ewoksdask
    :path: local

    **Start a Dask cluster with local machine resources**.

ewoksdask slurm
---------------

.. argparse::
    :module: ewoksdask.__main__
    :func: _create_argument_parser
    :prog: ewoksdask
    :path: slurm

    **Start a Dask cluster with Slurm resources**.
