Build and Test
==============

This section outlines how to build and test the ``p99-bluesky`` project.

Running Tests
-------------

To execute the test suite in your terminal, use ``tox``:

.. code:: bash

    tox -p

The ``-p`` flag enables parallel test execution, which significantly speeds up the process.

Understanding ``tox``
---------------------

In the ``p99-bluesky`` project, ``tox`` is configured to run a series of commands defined in the ``pyproject.toml`` file. These commands can also be executed individually in your terminal.

.. literalinclude:: ../../pyproject.toml
    :start-at: commands =
    :end-at: docs build/html

Code Formatting and Linting
---------------------------

To automatically correct code formatting and linting errors identified by ``ruff``, run the following command:

.. code:: bash

    ruff check ./src/p99_bluesky --fix

This command will apply fixes to the source code directly. It is recommended to run this command before committing changes.