Running bluesky on p99
======================

Athera
------

Athera service with blueAPI should already be running on kubernete sever and blueAPI control can be access `here <https://p99-blueapi.diamond.ac.uk/docs>`__.

For developer kubernete `deployment landing page is here. <https://k8s-p99.diamond.ac.uk/>`__

Local bluesky
-------------

For testing is is often easier to run tun bluesky locally.
A temple can be found in: 

.. code::

    src/p99-bluesky/tests/jupyter_tests/p99_bluesky_template.ipynb

it contrains all instructions on how to setup p99 to run basic bluesky plan.


To open the template run:

.. code::

    jupyter notebook ./tests/jupyter_tests/p99_bluesky_template.ipynb

.. warning::

    P99 hardware is only available on its own network. The easiest way is to ssh onto ws001-

.. note::

    Devices are imported from `dodal <https://github.com/DiamondLightSource/dodal/blob/main/src/dodal/beamlines/p99.py>`__,
    for more detail on how to create new devices see `here <https://blueskyproject.io/ophyd-async/main/tutorials/implementing-devices.html>`__.
    
    This `flowchart <https://diamondlightsource.github.io/dodal/main/how-to/make-new-ophyd-async-device.html>`__ can be useful when deciding what device it should be.
    
    It is also worth keeping in mind `device standard <https://diamondlightsource.github.io/dodal/main/reference/device-standards.html>`__ when creating a new device.

Local blueAPI
-------------