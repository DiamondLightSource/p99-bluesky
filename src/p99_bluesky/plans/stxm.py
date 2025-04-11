from collections.abc import Sequence
from math import floor

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from blueapi.core import MsgGenerator
from bluesky.preprocessors import (
    finalize_wrapper,
)
from bluesky.protocols import Readable
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator
from ophyd_async.epics.adcore import AreaDetector
from ophyd_async.epics.motor import Motor

from p99_bluesky.log import LOGGER
from p99_bluesky.plans.fast_scan import fast_scan_grid
from p99_bluesky.utility.utility import step_size_to_step_num

from ..plan_stubs import (
    check_within_limit,
    get_motor_positions,
    get_velocity_and_step_size,
    set_area_detector_acquire_time,
)


@attach_data_session_metadata_decorator()
def stxm_step(
    dets: Sequence[AreaDetector | Readable],
    count_time: float,
    x_step_motor: Motor,
    x_step_start: float,
    x_step_end: float,
    x_step_size: float,
    y_step_motor: Motor,
    y_step_start: float,
    y_step_end: float,
    y_step_size: float,
    home: bool = False,
    snake: bool = False,
    md: dict | None = None,
) -> MsgGenerator:
    """Effectively the standard Bluesky grid scan adapted to use step size.
     Added a centre option where it will move back to
      where it was before scan start.

    Parameters
    ----------
    det: Sequence[AreaDetector | Readable]
        Area detector.
    count_time: float
        detector count time.
    x_step_motor: Motor,
        Motors
    x_step_start: float,
        Starting position for x_step_motor
    x_step_size: float
        Step size for x motor
    step_end: float,
        Ending position for x_step_motor
    y_step_motor: Motor,
        Motor
    y_step_start: float,
        Start for scanning axis
    y_step_end: float,
        End for scanning axis
    y_step_size: float
        Step size for y motor
    home: bool = False,
        If true move back to position before it scan
    snake_axes: bool = True,
        If true, do grid scan without moving scan axis back to start position.
    md=None,

    """

    # check limit before doing anything
    yield from check_within_limit(
        [
            x_step_start,
            x_step_end,
        ],
        x_step_motor,
    )
    yield from check_within_limit(
        [
            y_step_start,
            y_step_end,
        ],
        y_step_motor,
    )
    # Dictionary to store clean up options
    clean_up_arg: dict = {}
    clean_up_arg["Home"] = home
    if home:
        # Add move back  positon to origin
        clean_up_arg["Origin"] = yield from get_motor_positions(
            x_step_motor, y_step_motor
        )
    main_det = dets[0]
    if isinstance(main_det, AreaDetector):
        # Set count time on detector
        yield from set_area_detector_acquire_time(main_det, acquire_time=count_time)
    # add 1 to step number to include the end point
    yield from finalize_wrapper(
        plan=bp.grid_scan(
            dets,
            x_step_motor,
            x_step_start,
            x_step_end,
            step_size_to_step_num(x_step_start, x_step_end, x_step_size) + 1,
            y_step_motor,
            y_step_start,
            y_step_end,
            step_size_to_step_num(y_step_start, y_step_end, y_step_size) + 1,
            snake_axes=snake,
            md=md,
        ),
        final_plan=clean_up(**clean_up_arg),
    )


@attach_data_session_metadata_decorator()
def stxm_fast(
    dets: list[AreaDetector | Readable],
    count_time: float,
    step_motor: Motor,
    step_start: float,
    step_end: float,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    plan_time: float,
    point_correction: float = 1,
    step_size: float | None = None,
    home: bool = False,
    snake_axes: bool = True,
    md: dict | None = None,
) -> MsgGenerator:
    """
    This initiates an STXM scan, targeting a maximum scan speed of around 10Hz.
     It calculates the number of data points achievable based on the detector's count
     time. If no step size is provided, the software aims for a uniform distribution
     of points across the scan area. The scanning motor's speed is then determined using
      the calculated point density. If the desired speed exceeds the motor's limit,
     the maximum speed is used. In this case, the step size is automatically adjusted
     to ensure the scan finishes close to the intended duration.

    Parameters
    ----------
    dets: list [Andor2Detector | Readable,]
        Area detector or any readable, the first dets is consider the main detector and
        the count time is set for this detector.
    count_time: float
        detector count time.
    step_motor: Motor,
        Motor for the slow axis
    step_start: float,
        Starting position for step axis
    step_end: float,
        Ending position for step axis
    scan_motor: Motor,
        Motor for the continuously moving axis
    scan_start: float,
        Start for scanning axis
    scan_end: float,
        End for scanning axis
    plan_time: float,
        How long it should take in second
    point_correction: float
        Scaling factor to allow adjustment of how many total points.
    step_size: float | None = None,
        Optional step size for the slow axis
    home: bool = False,
        If true move back to position before it scan
    snake_axes: bool = True,
        If true, do grid scan without moving scan axis back to start position.
    md=None,

    """
    clean_up_arg: dict = {}
    clean_up_arg["Home"] = home
    yield from check_within_limit(
        [
            scan_start,
            scan_end,
        ],
        scan_motor,
    )
    yield from check_within_limit(
        [
            step_start,
            step_end,
        ],
        step_motor,
    )
    # Add move back position to origin
    if home:
        clean_up_arg["Origin"] = yield from get_motor_positions(scan_motor, step_motor)

    scan_range = abs(scan_start - scan_end)
    scan_acc = yield from bps.rd(scan_motor.acceleration_time)
    scan_motor_speed = yield from bps.rd(scan_motor.velocity)
    step_range = abs(step_start - step_end)
    step_motor_speed = yield from bps.rd(step_motor.velocity)
    step_acc = yield from bps.rd(step_motor.acceleration_time)
    main_det = dets[0]
    if isinstance(main_det, AreaDetector):
        # Set count time on detector
        yield from set_area_detector_acquire_time(det=main_det, acquire_time=count_time)
        deadtime = main_det._controller.get_deadtime(count_time)
    else:
        deadtime = count_time

    # get number of data point possible after adjusting plan_time for step movement speed
    num_data_point_wo_acc = ((plan_time / deadtime) / (scan_range * step_range)) ** 0.5
    point_step_axis = floor(num_data_point_wo_acc * step_range)

    if point_step_axis < 1:
        point_step_axis = 1
    point_scan_axis = floor(num_data_point_wo_acc * (scan_range))
    print(f"ssa{point_step_axis}, fsa{point_scan_axis}, p{num_data_point_wo_acc:f}")
    step_mv_time = point_step_axis * step_acc * 2 + step_range / step_motor_speed

    if snake_axes:
        scan_mv_time = point_step_axis * (scan_acc * 2)
    else:
        scan_mv_time = point_scan_axis * (scan_acc * 2) + (point_scan_axis - 1) * (
            scan_range / scan_motor_speed + scan_acc * 2
        )  # Non-snake requires extra movement time
    """Rough adjustment of the num of data point possible including an over
    estimation of point per axis."""
    num_data_point = (
        ((plan_time - step_mv_time - scan_mv_time) / deadtime) / (scan_range * step_range)
    ) ** 0.5 * point_correction
    point_step_axis = floor(num_data_point * step_range)
    point_scan_axis = floor(num_data_point * (scan_range))
    print(point_scan_axis, point_step_axis)
    # Assuming ideal step size is evenly distributed points within the two axis.
    if step_size is not None:
        if step_size == 0:
            raise ValueError("Step_size is 0")
        ideal_step_size = abs(step_size)
    else:
        """The point correction factor is for correcting over
        estimation/extra motion time etc, defaulted to 1"""
        ideal_step_size = step_range / point_step_axis

    # ideal_velocity: speed that allow the required step size.
    if point_scan_axis <= 2:
        ideal_velocity = yield from bps.rd(scan_motor.max_velocity)
    else:
        ideal_velocity = scan_range / (
            scan_range / ideal_step_size * deadtime + scan_acc * 2
        )

    LOGGER.info(
        f"ideal step size = {ideal_step_size} velocity = {ideal_velocity}"
        + f" number of data point {num_data_point}"
    )
    velocity, ideal_step_size = yield from get_velocity_and_step_size(
        scan_motor, ideal_velocity, ideal_step_size
    )
    num_of_step = step_size_to_step_num(step_start, step_end, ideal_step_size)
    LOGGER.info(
        f" step size = {ideal_step_size}, {scan_motor.name}: velocity = {velocity}"
        + f", number of step = {num_of_step}."
    )
    # Set count time on detector
    if isinstance(main_det, AreaDetector):
        yield from set_area_detector_acquire_time(det=main_det, acquire_time=count_time)
    yield from finalize_wrapper(
        plan=fast_scan_grid(
            dets,
            step_motor,
            step_start,
            step_end,
            num_of_step,
            scan_motor,
            scan_start,
            scan_end,
            velocity,
            snake_axes=snake_axes,
            md=md,
        ),
        final_plan=clean_up(**clean_up_arg),
    )


def clean_up(**kwargs: dict):
    LOGGER.info(f"Clean up: {list(kwargs)}")
    if kwargs["Home"]:
        # move motor back to stored position
        yield from bps.mov(*kwargs["Origin"])
