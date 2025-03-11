Running bluesky on p99
======================


Athena
------

Athena service with blueAPI should already be running on Kubernetes sever and blueAPI control can be access `here <https://p99-blueapi.diamond.ac.uk/docs>`__.

For developer Kubernetes deployment landing page is `here. <https://k8s-p99.diamond.ac.uk/>`__

Local bluesky
-------------

For testing it is often easier to run bluesky locally.
A template with p99 hardware setting can be found in:
``src/p99-bluesky/tests/jupyter_tests/p99_bluesky_template.ipynb``

To open the template run:

.. code::

    jupyter notebook ./tests/jupyter_tests/p99_bluesky_template.ipynb

.. warning::

    P99 hardware is only available on its own network. The easiest way is to run test is make use of p99-ws001 via ssh:

    .. code::

        ssh -X p99-ws001



.. note::

    Devices are imported from `dodal <https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/beamlines/p99.py>`__,
    for more detail on how to create new devices see `here <https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html>`__.
    
    This `flowchart <https://diamondlightsource.github.io/dodal/main/how-to/make-new-ophyd-async-device.html>`__ can be useful when deciding what device it should be.
    
    It is also worth keeping in mind `device standard <https://diamondlightsource.github.io/dodal/main/reference/device-standards.html>`__ when creating a new device.

Local blueAPI
-------------

To run blueAPI locally you will need to start an RabbitMQ instance, the easiest way is make use of blueAPI script `here <https://diamondlightsource.github.io/blueapi/main/tutorials/run-bus.html>`__

With RabbitMQ running run:

.. code::

    blueapi --config ./src/yaml_config/blueapi_config.yaml serve

This will start blueAPI with p99 configuration. To modify the configuration you can make change to ``/workspaces/p99-bluesky/src/yaml_config/blueapi_config.yaml``.

.. literalinclude:: ../../src/yaml_config/blueapi_config.yaml


.. tip::
    
    To add devices and plans you can insert extra sources:

    for devices:

    .. code::

        env:
            sources:
            - kind: deviceFunctions
                module: <device path>

    for plans:

    .. code::

        env:
            sources:
            - kind: planFunctions
                module: <plans path>

.. note::

    Plans must have return typing ``MsgGenerator`` and complete typing hint for blueAPI to pick up, see example:  

    .. literalinclude:: ../../src/p99_bluesky/plans/stxm.py
        :start-at: def stxm_fast
        :end-at: -> MsgGenerator:

    
