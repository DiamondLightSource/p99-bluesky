Build and test
==============

To run test in terminal:

.. code::

    tox -p


-p will allow tox builds to be run in parallel.

.. note::

    In p99 tox is a collect of commands which you can run seperatly in terminal.

    .. literalinclude:: ../../pyproject.toml
        :start-at: commands =
        :end-at: docs build/html

    You can also auto correct pre-commit error by running:

    .. code::

        ruff check ./src/p99_bluesky --fix


        dfjsmdklfm 