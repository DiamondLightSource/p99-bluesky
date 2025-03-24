import pytest
from blueapi.client.client import BlueapiClient
from blueapi.config import ApplicationConfig, RestConfig, StompConfig
from blueapi.worker.task import Task
from bluesky_stomp.models import BasicAuthentication

BEAMLINE = "p99"


@pytest.fixture
def task_definition() -> dict[str, Task]:
    return {
        "stxm_step": Task(
            name="stxm_step",
            params={
                "det": "andor2_point",
                "count_time": 0.1,
                "x_step_motor": "sample_stage.x",
                "x_step_start": -0.1,
                "x_step_end": 0.1,
                "x_step_size": 0.05,
                "y_step_motor": "sample_stage.y",
                "y_step_start": -0.1,
                "y_step_end": 0.1,
                "y_step_size": 0.05,
            },
        ),
    }


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--password", action="store", default="")


@pytest.fixture
def config(request: pytest.FixtureRequest) -> ApplicationConfig:
    if BEAMLINE == "p99":
        password = request.config.getoption("--password")
        return ApplicationConfig(
            stomp=StompConfig(
                host="172.23.177.208",
                auth=BasicAuthentication(username="p99", password=password),  # type: ignore
            ),
            api=RestConfig(host="p99-blueapi.diamond.ac.uk", port=443, protocol="https"),
        )
    else:
        return ApplicationConfig(
            stomp=StompConfig(
                host="localhost",
                auth=BasicAuthentication(username="guest", password="guest"),  # type: ignore
            )
        )


# This client will use authentication if a valid cached token is found
@pytest.fixture
def client(config: ApplicationConfig) -> BlueapiClient:
    return BlueapiClient.from_config(config=config)
