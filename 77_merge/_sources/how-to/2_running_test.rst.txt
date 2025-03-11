Build and test
==============

To run test in terminal:

.. code::

    tox -p


-p will allow tox builds to be run in parallel.

.. note::

    In p99 tox is a collect of commands which you can run seperatly in terminal.

    .. code:: 

        commands =
        pre-commit: pre-commit run --all-files {posargs}
        type-checking: pyright src tests {posargs}
        tests: pytest --cov=p99_bluesky --cov-report term --cov-report xml:cov.xml {posargs}
        docs: sphinx-{posargs:build -EW --keep-going} -T docs build/html

    You can also auto correct pre-commit error by running:

    .. code::

        ruff check ./src/p99_bluesky --fix



