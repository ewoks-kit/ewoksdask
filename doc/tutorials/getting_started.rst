Getting started
===============

Install requirements

.. code-block:: bash

    pip install ewoksdask

Execute a workflow

.. code-block:: python

    from ewoksdask import execute_graph

    result = execute_graph("/path/to/graph.json")
