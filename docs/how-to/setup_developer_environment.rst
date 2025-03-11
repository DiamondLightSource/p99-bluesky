Setup Developer Environment
===========================

Clone the repository
--------------------

To Clone the repository locally use `Git <https://git-scm.com/downloads>`__:

SSH:


.. code::

    git clone git@github.com:DiamondLightSource/p99-bluesky.git

or HTTPS:

.. code::

    git clone https://github.com/DiamondLightSource/p99-bluesky.git

.. tip::

    SSH is recommended and to setup ssh key for git, follow the instruction `here. <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account>`__


Install dependencies
--------------------

You can choose to either develop on the host machine using a `venv` (which requires python 3.10 or later) or to run in a container under `VSCode <https://code.visualstudio.com/>`__.


.. tab-set::

    .. tab-item:: VSCode devcontainer

        At any diamond teminal type:
        
        .. code::

            module load vscode
            code ./p99-bluesky

        Once vscode is running, hold ctri+shift+p or go to the search bar and type:

        .. code::
        
            > Dev containers:Reubuild container

        This will buiild the Dev container using Docker by default, to change the setting hold ctri+shit+p again and type:
        
        .. code::
        
            > Dev containers:settings

        In setting under user change:
        
        .. code::
        
            Dev>Contrainers:Docker Path 
        
        to podman.

        .. tip::
        
            For working on window you can make use of wsl and docker destop more detail is `here. <https://code.visualstudio.com/docs/devcontainers/containers>`__

            More detail on how to setup vscode outside diamond is `here. <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers>`__


        .. note::

            If you are at DLS and podman is not setup you can find more detail on `setting up podman and its fix for devcontainer features <https://dev-portal.diamond.ac.uk/guide/containers/tutorials/podman/#enable-use-of-vscode-features) and then follow [these instructions](https://dev-portal.diamond.ac.uk/guide/containers/tutorials/devcontainer/>`__.



    .. tab-item:: Local virtualenv

        .. code::

            python3.11 -m venv venv_p99
            source venv_p99/bin/activate
            cd p99-bluesky
            pip install -e '.[dev]'d