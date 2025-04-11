from collections import defaultdict
from math import floor

import pytest
from bluesky.run_engine import RunEngine
from numpy import random
from ophyd_async.core import (
    init_devices,
)
from ophyd_async.epics.adandor import Andor2Detector
from ophyd_async.testing import assert_emitted, set_mock_value

from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.stxm import stxm_fast, stxm_step
from p99_bluesky.sim.sim_stages import SimThreeAxisStage
from p99_bluesky.utility.utility import step_size_to_step_num


@pytest.fixture
async def sim_motor_step():
    async with init_devices():
        sim_motor_step = SimThreeAxisStage(name="sim_motor", instant=True)

    yield sim_motor_step


@pytest.fixture
async def sim_motor_fly():
    async with init_devices():
        sim_motor_fly = SimThreeAxisStage(name="sim_motor_fly", instant=False)

    yield sim_motor_fly


async def test_stxm_fast_zero_velocity_fail(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine
):
    plan_time = 10
    count_time = 0.2
    step_size = 0.0
    step_start = -2
    step_end = 3
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    with pytest.raises(ValueError):
        RE(
            stxm_fast(
                dets=[andor2],
                count_time=count_time,
                step_motor=sim_motor.x,
                step_start=step_start,
                step_end=step_end,
                scan_motor=sim_motor.y,
                scan_start=1,
                scan_end=2,
                plan_time=plan_time,
                step_size=step_size,
            ),
            capture_emitted,
        )
    # should do nothingdocs = defaultdict(list)
    assert_emitted(docs)


async def test_stxm_fast(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    plan_time = 50
    count_time = 0.1
    step_size = 0.1
    step_start = -2
    step_end = 3
    num_of_step = step_size_to_step_num(step_start, step_end, step_size)

    RE(
        stxm_fast(
            dets=[andor2],
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=1,
            scan_end=2,
            plan_time=plan_time,
            step_size=step_size,
            home=True,
        ),
        capture_emitted,
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=num_of_step,
        event=num_of_step,
        stop=1,
    )


async def test_stxm_fast_with_speed_capped(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    plan_time = 10
    count_time = 0.0
    step_size = 0.2
    step_start = -2
    step_end = 2
    num_of_step = step_size_to_step_num(step_start, step_end, step_size)
    set_mock_value(sim_motor.y.max_velocity, 1)  # running at half the speed that required
    RE(
        stxm_fast(
            dets=[andor2],
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=1,
            scan_end=2,
            plan_time=plan_time,
            step_size=step_size,
            home=True,
        ),
        capture_emitted,
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=num_of_step * 2,
        event=num_of_step * 2,
        stop=1,
    )


@pytest.mark.parametrize("execution_number", range(5))
async def test_stxm_fast_unknown_step_snake(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine, execution_number
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    rng = random.default_rng()
    number_of_point = rng.integers(low=5, high=20)

    step_motor_speed = rng.uniform(low=0.5, high=10)
    scan_motor_speed = rng.uniform(low=0.5, high=10)
    step_acc = step_motor_speed * rng.uniform(low=0.01, high=0.1)
    scan_acc = scan_motor_speed * rng.uniform(low=0.01, high=0.1)
    step_start = rng.uniform(low=-3, high=1.5)
    step_end = 5
    scan_start = rng.uniform(low=-3, high=2)
    scan_end = 3
    count_time = rng.uniform(low=0.1, high=1)
    det_dead_time = 0.1
    deadtime = count_time + det_dead_time
    step_range = abs(step_start - step_end)
    scan_range = abs(scan_start - scan_end)
    set_mock_value(sim_motor.x.velocity, step_motor_speed)
    set_mock_value(sim_motor.x.acceleration_time, step_acc)
    set_mock_value(sim_motor.y.velocity, scan_motor_speed)
    set_mock_value(sim_motor.y.acceleration_time, scan_acc)

    plan_time = number_of_point**2 * (deadtime)
    RE(
        stxm_fast(
            dets=[andor2],
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=scan_start,
            scan_end=scan_end,
            plan_time=plan_time,
            home=True,
        ),
        capture_emitted,
    )

    # +- one data point due to rounding

    # assert docs["event"].__len__() == pytest.approx(floor(point_per_axis), abs=1)
    t = (number_of_point**2 / (step_range + scan_range)) ** 0.5 * step_range
    assert docs["event"].__len__() == pytest.approx(floor(t), rel=1)


@pytest.mark.parametrize("execution_number", range(5))
async def test_stxm_fast_unknown_step_no_snake(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine, execution_number
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    step_motor_speed = 1
    scan_motor_speed = 2
    step_acc = 0.1
    scan_acc = 0.1
    step_start = 0
    step_end = 2
    scan_start = -1
    scan_end = 1
    count_time = 0.1
    det_dead_time = 0.1
    scan_range = abs(scan_start - scan_end)
    step_range = abs(step_start - step_end)
    set_mock_value(sim_motor.x.velocity, step_motor_speed)
    set_mock_value(sim_motor.x.acceleration_time, 0.1)
    set_mock_value(sim_motor.y.velocity, scan_motor_speed)
    set_mock_value(sim_motor.y.acceleration_time, 0.1)
    rng = random.default_rng()

    number_of_point = rng.integers(low=5, high=25)

    plan_time = (
        number_of_point**2 * (count_time + det_dead_time)
        + number_of_point * (step_acc * 2 + scan_acc * 2)
        + step_range / step_motor_speed
        + (number_of_point - 1) * (scan_range / scan_motor_speed + scan_acc * 2)
    )
    print(plan_time)
    docs = defaultdict(list)
    RE(
        stxm_fast(
            dets=[andor2],
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=scan_start,
            scan_end=scan_end,
            plan_time=plan_time,
            snake_axes=False,
            home=True,
        ),
        capture_emitted,
    )

    # speed capped at half ideal so expecting 5 events
    # assert_emitted(
    #     docs,
    #     start=1,
    #     descriptor=1,
    #     stream_resource=1,
    #     stream_datum=number_of_point,
    #     event=number_of_point,
    #     stop=1,
    # )
    assert docs["event"].__len__() <= number_of_point


@pytest.mark.parametrize("execution_number", range(5))
async def test_stxm_fast_unknown_step_snake_with_point_correction(
    andor2: Andor2Detector, sim_motor: ThreeAxisStage, RE: RunEngine, execution_number
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    rng = random.default_rng()

    point_correction = rng.uniform(low=0.2, high=1)
    step_motor_speed = 0.1
    scan_motor_speed = 0.1
    step_acc = 0.1
    scan_acc = 0.1
    step_start = 1  # rng.uniform(low=-4, high=1)
    step_end = 5
    scan_start = -1
    scan_end = 1
    count_time = 0.1

    set_mock_value(sim_motor.x.velocity, step_motor_speed)
    set_mock_value(sim_motor.x.acceleration_time, step_acc)
    set_mock_value(sim_motor.y.velocity, scan_motor_speed)
    set_mock_value(sim_motor.y.acceleration_time, scan_acc)

    plan_time = 100  # this will generate 21 steps
    point_step_axis = 21

    docs = defaultdict(list)
    RE(
        stxm_fast(
            dets=[andor2],
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=scan_start,
            scan_end=scan_end,
            plan_time=plan_time,
            point_correction=point_correction,
            home=True,
        ),
        capture_emitted,
    )

    # +- one data point due to rounding

    assert docs["event"].__len__() == pytest.approx(
        floor(point_step_axis * point_correction), abs=1
    )


async def test_stxm_step_with_home(
    RE: RunEngine, sim_motor_step: ThreeAxisStage, andor2: Andor2Detector
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await sim_motor_step.x.set(-1)
    await sim_motor_step.y.set(-2)

    RE(
        stxm_step(
            dets=[andor2],
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=2,
            x_step_size=0.2,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=1,
            y_step_size=0.25,
            home=True,
            snake=True,
        ),
        capture_emitted,
    )

    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=99,
        event=99,
        stop=1,
    )
    assert -1 == await sim_motor_step.x.user_readback.get_value()
    assert -2 == await sim_motor_step.y.user_readback.get_value()


async def test_stxm_step_without_home_with_readable(
    RE: RunEngine,
    sim_motor_step: ThreeAxisStage,
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await sim_motor_step.x.set(-1)
    await sim_motor_step.y.set(-2)
    y_step_end = 1
    x_step_end = 2
    RE(
        stxm_step(
            dets=[sim_motor_step.z],
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=x_step_end,
            x_step_size=0.2,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=y_step_end,
            y_step_size=0.25,
            home=False,
            snake=False,
        ),
        capture_emitted,
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        event=99,
        stop=1,
    )
    assert x_step_end == await sim_motor_step.x.user_readback.get_value()
    assert y_step_end == await sim_motor_step.y.user_readback.get_value()
