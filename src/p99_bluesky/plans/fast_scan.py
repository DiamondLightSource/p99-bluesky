from typing import Any

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from blueapi.core import MsgGenerator
from bluesky.preprocessors import (
    finalize_wrapper,
)
from numpy import linspace
from ophyd_async.core.utils import (
    CalculatableTimeout,
    CalculateTimeout,
)
from ophyd_async.epics.motion import Motor
from pydantic import BaseModel, Field

from p99_bluesky.log import LOGGER
from p99_bluesky.plan_stubs.motor_plan import check_within_limit


# Remove once ophyd release
class FlyMotorInfo(BaseModel):
    """Minimal set of information required to fly a motor:"""

    #: Absolute position of the motor once it finishes accelerating to desired
    #: velocity, in motor EGUs
    start_position: float = Field(frozen=True)

    #: Absolute position of the motor once it begins decelerating from desired
    #: velocity, in EGUs
    end_position: float = Field(frozen=True)

    #: Time taken for the motor to get from start_position to end_position, excluding
    #: run-up and run-down, in seconds.
    time_for_move: float = Field(frozen=True, gt=0)

    #: Maximum time for the complete motor move, including run up and run down.
    #: Defaults to `time_for_move` + run up and run down times + 10s.
    timeout: CalculatableTimeout = Field(frozen=True, default=CalculateTimeout)


def fast_scan_1d(
    dets: list[Any],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
) -> MsgGenerator:
    """
    One axis fast scan, using _fast_scan_1d.

    Parameters
    ----------
    detectors : list
        list of 'readable',triggerable  objects
    motor : Motor (moveable, readable)

    start: float
        starting position.
    end: float,
        ending position

    motor_speed: Optional[float] = None,
        The speed of the motor during scan
    """

    @bpp.stage_decorator(dets)
    @bpp.run_decorator()
    def inner_fast_scan_1d(
        dets: list[Any],
        motor: Motor,
        start: float,
        end: float,
        motor_speed: float | None = None,
    ):
        yield from check_within_limit([start, end], motor)
        yield from _fast_scan_1d(dets, motor, start, end, motor_speed)

    yield from finalize_wrapper(
        plan=inner_fast_scan_1d(dets, motor, start, end, motor_speed),
        final_plan=clean_up(),
    )


def fast_scan_grid(
    dets: list[Any],
    step_motor: Motor,
    step_start: float,
    step_end: float,
    num_step: int,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    motor_speed: float | None = None,
    snake_axes: bool = False,
) -> MsgGenerator:
    """
    Same as fast_scan_1d with an extra axis to step through forming a grid.

     Parameters
     ----------
     detectors : list
         list of 'readable' objects
     step_motor : Motor (moveable, readable)
     scan_motor:  Motor (moveable, readable)
     start: float
         starting position.
     end: float,
         ending position

     motor_speed: Optional[float] = None,
         The speed of the motor during scan
    """

    @bpp.stage_decorator(dets)
    @bpp.run_decorator()
    def inner_fast_scan_grid(
        dets: list[Any],
        step_motor: Motor,
        step_start: float,
        step_end: float,
        num_step: int,
        scan_motor: Motor,
        scan_start: float,
        scan_end: float,
        motor_speed: float | None = None,
        snake_axes: bool = False,
    ):
        yield from check_within_limit([step_start, step_end], step_motor)
        yield from check_within_limit([scan_start, scan_end], scan_motor)
        steps = linspace(step_start, step_end, num_step, endpoint=True)
        if snake_axes:
            for cnt, step in enumerate(steps):
                yield from bps.mv(step_motor, step)
                if cnt % 2 == 0:
                    yield from _fast_scan_1d(
                        dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                    )
                else:
                    yield from _fast_scan_1d(
                        dets + [step_motor], scan_motor, scan_end, scan_start, motor_speed
                    )
        else:
            for step in steps:
                yield from bps.mv(step_motor, step)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                )

    yield from finalize_wrapper(
        plan=inner_fast_scan_grid(
            dets,
            step_motor,
            step_start,
            step_end,
            num_step,
            scan_motor,
            scan_start,
            scan_end,
            motor_speed,
            snake_axes,
        ),
        final_plan=clean_up(),
    )


def _fast_scan_1d(
    dets: list[Any],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
) -> MsgGenerator:
    """
    The logic for one axis fast scan, used in fast_scan_1d and fast_scan_grid

    In this scan:
    1) The motor moves to the starting point.
    2) The motor speed is changed
    3) The motor is set in motion toward the end point
    4) During this movement detectors are triggered and read out until
      the endpoint is reached or stopped.
    5) Clean up, reset motor speed.

    Note: This is purely software triggering which result in variable accuracy.
    However, fast scan does not require encoder and hardware setup and should
    work for all motor. It is most frequently use for alignment and
    slow motion measurements.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    motor : Motor (moveable, readable)

    start: float
        starting position.
    end: float,
        ending position

    motor_speed: Optional[float] = None,
        The speed of the motor during scan
    """

    # read the current speed and store it
    old_speed = yield from bps.rd(motor.velocity)

    def inner_fast_scan_1d(
        dets: list[Any],
        motor: Motor,
        start: float,
        end: float,
        motor_speed: float | None = None,
    ):
        LOGGER.info(f"Moving {motor.name} to start position = {start}.")
        yield from bps.mv(motor, start)  # move to start

        if motor_speed:
            LOGGER.info(f"Set {motor.name} speed = {motor_speed}.")
            yield from bps.abs_set(motor.velocity, motor_speed)

        LOGGER.info(f"Set {motor.name} to end position({end}) and begin scan.")
        yield from bps.abs_set(motor.user_setpoint, end)
        # yield from bps.wait_for(motor.motor_done_move, False)
        done = False

        while not done:
            yield from bps.trigger_and_read(dets + [motor])
            done = yield from bps.rd(motor.motor_done_move)
            yield from bps.checkpoint()

    yield from finalize_wrapper(
        plan=inner_fast_scan_1d(dets, motor, start, end, motor_speed),
        final_plan=reset_speed(old_speed, motor),
    )


def reset_speed(old_speed, motor: Motor):
    LOGGER.info(f"Clean up: setting motor speed to {old_speed}.")
    if old_speed:
        yield from bps.abs_set(motor.velocity, old_speed)


def clean_up():
    LOGGER.info("Clean up")
    # possibly use to move back to starting position.
    yield from bps.null()


"""
 Future: replace _fast_scan_1d with below to take advantage of ophyd aysnc motor,
  I am not 100% sure but I think there is a bug with the motor's set,it never entre
    the watch loop as move_status goes true almost immediately:move_status =
      self.user_setpoint.set(   new_position, wait=True, timeout=timeout)async
        for current_position in observe_value(self.user_readback, done_status=move_status)
"""
# def _fly_scan_1d(
#     dets: list[Any],
#     motor: Motor,
#     start: float,
#     end: float,
#     motor_speed: float | None = None,
# ) -> MsgGenerator:
#     # read the current speed and store it
#     old_speed = yield from bps.rd(motor.velocity)

#     def inner_fast_scan_1d(
#         dets: list[Any],
#         motor: Motor,
#         start: float,
#         end: float,
#         motor_speed: float | None = None,
#     ):
#         LOGGER.info(f"Moving {motor.name} to start position = {start}.")
#         yield from bps.mv(motor, start)  # move to start

#         if motor_speed:
#             LOGGER.info(f"Set {motor.name} speed = {motor_speed}.")
#             yield from bps.abs_set(motor.velocity, motor_speed)
#         else:
#             motor_speed = yield from bps.rd(motor.velocity)

#         LOGGER.info(f"Set {motor.name} to end position({end}) and begin scan.")
#         grp = short_uid("prepare")
#         fly_info = FlyMotorInfo(
#             start_position=start,
#             end_position=end,
#             time_for_move=abs(start - end) / motor_speed,
#         )
#         yield from bps.prepare(motor, fly_info, group=grp, wait=True)
#         yield from bps.kickoff(motor, group=grp, wait=True)

#         done = yield from bps.complete(motor)
#         LOGGER.info(f"flying motor =  {motor.name} at speed =({motor_speed})")
#         while not done.done:
#             yield from bps.trigger_and_read(dets + [motor])
#             yield from bps.checkpoint()

#     yield from finalize_wrapper(
#         plan=inner_fast_scan_1d(dets, motor, start, end, motor_speed),
#         final_plan=reset_speed(old_speed, motor),
#     )
