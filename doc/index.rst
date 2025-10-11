ewoksdask |version|
===================

*ewoksdask* provides distributed task scheduling for `ewoks <https://ewoks.readthedocs.io/>`_ workflows.

*ewoksdask* has been developed by the `Software group <http://www.esrf.fr/Instrumentation/software>`_ of the `European Synchrotron <https://www.esrf.fr/>`_.

Getting started
---------------

Install requirements

.. code-block:: bash

    pip install ewoksdask

Execute a workflow

.. code-block:: python

    from ewoksdask import execute_graph

    result = execute_graph("/path/to/graph.json")

Run the tests

.. code-block:: bash

    pip install ewoksdask[test]
    pytest --pyargs ewoksdask.tests

.. toctree::
    :hidden:

    howtoguides/index
    reference/index
