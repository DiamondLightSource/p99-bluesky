# Installation

## Prerequisites

Before installing, ensure you have Python 3.10 or later. You can check your Python version by running the following command in your terminal:

```bash
python3 --version
```

## Create a virtual environment

It's highly recommended to install ``p99_bluesky`` within a virtual environment. This isolates the project's dependencies and prevents conflicts with other Python installations.

```bash
python3 -m venv /path/to/venv
```

Replace /path/to/your/venv with the desired directory for your virtual environment (e.g., ~/p99_venv).

## Activate the virtual environment:

```bash
source /path/to/venv/bin/activate
```

(On Windows, use \path\to\your\venv\Scripts\activate)

Once activated, your terminal prompt will typically change to indicate that the virtual environment is active.

## Installing the p99_bluesky Library

With the virtual environment activated, you can now install ``p99_bluesky`` using ``pip``:

```bash
$ python3 -m pip install p99_bluesky
```

To install the latest development version directly from GitHub:

```bash
$ python3 -m pip install git+https://github.com/Relm-Arrowny/p99_bluesky.git
```
##Verifying the Installation

After installation, you can verify that `p99_bluesky` is installed correctly and check its version by running:

```bash
$ p99_bluesky --version
```
This command should display the installed version number.