"""Comment out blueapi until it catch up with pydantic v3"""

# from dodal.common.beamlines.beamline_utils import device_instantiation
# from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
# from dodal.log import set_beamline as set_log_beamline
# from dodal.utils import get_beamline_name

# from p99_bluesky.devices.p99.sample_stage import FilterMotor, SampleAngleStage
# from p99_bluesky.devices.stages import ThreeAxisStage

# BL = get_beamline_name("99P")
# set_log_beamline(BL)
# set_utils_beamline(BL)


# def sample_angle_stage(
#     wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
# ) -> SampleAngleStage:
#     """Sample stage for p99"""

#     return device_instantiation(
#         SampleAngleStage,
#         prefix="-MO-STAGE-01:",
#         name="sample_angle_stage",
#         wait=wait_for_connection,
#         fake=fake_with_ophyd_mock,
#     )


# def sample_stage_filer(
#     wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
# ) -> FilterMotor:
#     """Sample stage for p99"""

#     return device_instantiation(
#         FilterMotor,
#         prefix="-MO-STAGE-02:MP:SELECT",
#         name="sample_stage_filer",
#         wait=wait_for_connection,
#         fake=fake_with_ophyd_mock,
#     )


# def sample_xyz_stage(
#     wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
# ) -> ThreeAxisStage:
#     return device_instantiation(
#         ThreeAxisStage,
#         prefix="-MO-STAGE-02:",
#         name="sample_xyz_stage",
#         wait=wait_for_connection,
#         fake=fake_with_ophyd_mock,
#     )


# def sample_lab_xyz_stage(
#     wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
# ) -> ThreeAxisStage:
#     return device_instantiation(
#         ThreeAxisStage,
#         prefix="-MO-STAGE-02:LAB:",
#         name="sample_lab_xyz_stage",
#         wait=wait_for_connection,
#         fake=fake_with_ophyd_mock,
#     )
