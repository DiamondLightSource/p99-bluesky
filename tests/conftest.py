import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    FilenameProvider,
    StaticFilenameProvider,
    StaticPathProvider,
    callback_on_mock_put,
    set_mock_value,
)
from super_state_machine.errors import TransitionError

from p99_bluesky.devices import Andor2Ad, Andor3Ad
from p99_bluesky.devices.stages import ThreeAxisStage
from soft_motor import SoftThreeAxisStage

RECORD = str(Path(__file__).parent / "panda" / "db" / "panda.db")
INCOMPLETE_BLOCK_RECORD = str(
    Path(__file__).parent / "panda" / "db" / "incomplete_block_panda.db"
)
INCOMPLETE_RECORD = str(Path(__file__).parent / "panda" / "db" / "incomplete_panda.db")
EXTRA_BLOCKS_RECORD = str(
    Path(__file__).parent / "panda" / "db" / "extra_blocks_panda.db"
)


@pytest.fixture(scope="session")
def RE(request):
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    RE = RunEngine({}, call_returns_result=True, loop=loop)

    def clean_event_loop():
        if RE.state not in ("idle", "panicked"):
            try:
                RE.halt()
            except TransitionError:
                pass
        loop.call_soon_threadsafe(loop.stop)
        RE._th.join()
        loop.close()

    request.addfinalizer(clean_event_loop)
    return RE


@pytest.fixture
async def normal_coroutine() -> Callable[[], Any]:
    async def inner_coroutine():
        await asyncio.sleep(0.01)

    return inner_coroutine


@pytest.fixture
async def failing_coroutine() -> Callable[[], Any]:
    async def inner_coroutine():
        await asyncio.sleep(0.01)
        raise ValueError()

    return inner_coroutine


@pytest.fixture(scope="session")
def xyz_motor(fake_99):
    with DeviceCollector(mock=False):
        xyz_motor = SoftThreeAxisStage("p99-MO-STAGE-02:", name="xyz_motor")
    yield xyz_motor


@pytest.fixture
def static_filename_provider():
    return StaticFilenameProvider("ophyd_async_tests")


@pytest.fixture
def static_path_provider_factory(tmp_path: Path):
    def create_static_dir_provider_given_fp(fp: FilenameProvider):
        return StaticPathProvider(fp, tmp_path)

    return create_static_dir_provider_given_fp


@pytest.fixture
def static_path_provider(
    static_path_provider_factory,
    static_filename_provider: FilenameProvider,
):
    return static_path_provider_factory(static_filename_provider)


# area detector that is use for testing
@pytest.fixture
async def andor2(static_path_provider: StaticPathProvider) -> Andor2Ad:
    async with DeviceCollector(mock=True):
        andor2 = Andor2Ad("p99", static_path_provider, "andor2")

    set_mock_value(andor2._controller._drv.array_size_x, 10)
    set_mock_value(andor2._controller._drv.array_size_y, 20)
    set_mock_value(andor2.hdf.file_path_exists, True)
    set_mock_value(andor2.hdf.num_captured, 0)
    set_mock_value(andor2.hdf.file_path, str(static_path_provider._directory_path))
    set_mock_value(
        andor2.hdf.full_file_name,
        str(static_path_provider._directory_path) + "/test-andor2-hdf0",
    )

    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(0, 10000)
    callback_on_mock_put(
        andor2._writer.hdf.capture,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.capture, value=True),
    )

    callback_on_mock_put(
        andor2.drv.acquire,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.num_captured, rbv_mocks.get()),
    )

    return andor2


@pytest.fixture
async def andor3(static_path_provider: StaticPathProvider) -> Andor3Ad:
    async with DeviceCollector(mock=True):
        andor3 = Andor3Ad("p99", static_path_provider, "andor3")

    set_mock_value(andor3._controller._drv.array_size_x, 10)
    set_mock_value(andor3._controller._drv.array_size_y, 20)
    set_mock_value(andor3.hdf.file_path_exists, True)
    set_mock_value(andor3.hdf.num_captured, 0)
    set_mock_value(andor3.hdf.file_path, str(static_path_provider._directory_path))
    set_mock_value(
        andor3.hdf.full_file_name,
        str(static_path_provider._directory_path) + "/test-andor3-hdf0",
    )

    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(0, 10000)
    callback_on_mock_put(
        andor3._writer.hdf.capture,
        lambda *_, **__: set_mock_value(andor3._writer.hdf.capture, value=True),
    )

    callback_on_mock_put(
        andor3.drv.acquire,
        lambda *_, **__: set_mock_value(andor3._writer.hdf.num_captured, rbv_mocks.get()),
    )

    return andor3


@pytest.fixture
async def sim_motor():
    async with DeviceCollector(mock=True):
        sim_motor = ThreeAxisStage("BLxxI-MO-TABLE-01:X", name="sim_motor")
    set_mock_value(sim_motor.x.velocity, 2.78)
    set_mock_value(sim_motor.x.high_limit_travel, 8.168)
    set_mock_value(sim_motor.x.low_limit_travel, -8.888)
    set_mock_value(sim_motor.x.user_readback, 1)
    set_mock_value(sim_motor.x.motor_egu, "mm")
    set_mock_value(sim_motor.x.motor_done_move, True)
    set_mock_value(sim_motor.x.max_velocity, 10)

    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.high_limit_travel, 5.168)
    set_mock_value(sim_motor.y.low_limit_travel, -5.888)
    set_mock_value(sim_motor.y.user_readback, 0)
    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.velocity, 2.88)
    set_mock_value(sim_motor.y.motor_done_move, True)
    set_mock_value(sim_motor.y.max_velocity, 10)

    set_mock_value(sim_motor.z.motor_egu, "mm")
    set_mock_value(sim_motor.z.high_limit_travel, 5.168)
    set_mock_value(sim_motor.z.low_limit_travel, -5.888)
    set_mock_value(sim_motor.z.user_readback, 0)
    set_mock_value(sim_motor.z.motor_egu, "mm")
    set_mock_value(sim_motor.z.velocity, 2.88)
    set_mock_value(sim_motor.z.motor_done_move, True)
    set_mock_value(sim_motor.z.max_velocity, 10)

    yield sim_motor
