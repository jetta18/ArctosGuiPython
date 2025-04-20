"""
File: core/homing.py

This module provides functions to home the robot axes and move them into a safe sleep pose.
Extended to support six axes with configurable offsets, speeds, and accelerations.
"""
import time
import logging
from typing import Any, Dict

from utils.settings_manager import SettingsManager

# Initialize module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# List of motor axes (1-based indexing corresponds to arctos.servos[axis-1])
MOTOR_IDS = [1, 2, 3, 4, 5, 6]

# Homing sequence: start at joint 6 and end at joint 1
HOMING_SEQUENCE = list(reversed(MOTOR_IDS))

# Predefined zero positions for each axis (raw units)
# Axis 3: -2410, Axis 2: -3300, Axis 1: -1038 (as per existing calibration)
ZERO_POSITIONS: Dict[int, int] = {
    1: -1038,
    2: -3300,
    3: -2410,
    4:    0,  # TODO: calibrate zero position for axis 4
    5:    0,  # TODO: calibrate zero position for axis 5
    6:    0,  # TODO: calibrate zero position for axis 6
}

# Predefined sleep positions for each axis (raw units)
SLEEP_POSITIONS: Dict[int, int] = {
    1: 0,  # TODO: set actual sleep pose for axis 1
    2: 0,  # TODO: set actual sleep pose for axis 2
    3: 0,  # TODO: set actual sleep pose for axis 3
    4: 0,  # TODO: set actual sleep pose for axis 4
    5: 0,  # TODO: set actual sleep pose for axis 5
    6: 0,  # TODO: set actual sleep pose for axis 6
}


def move_to_zero_pose(arctos: Any, settings_manager: SettingsManager) -> None:
    """
    Perform the homing routine for all axes in reverse order (joint 6 to 1):
    1. Move to the home switch via built-in b_go_home().
    2. Move to the configured zero position plus user offset.
    3. Set the current axis position to zero in software.

    Args:
        arctos: Robot controller instance providing servo control methods.
        settings_manager: SettingsManager instance for retrieving homing offsets.

    Returns:
        None
    """
    logger.info("Starting homing process for all axes (6->1)")

    # Retrieve settings for offsets, speeds, and accelerations
    offsets: Dict[int, int] = settings_manager.get("homing_offsets", {})
    speeds: Dict[int, int] = settings_manager.get("joint_speeds", {})
    accelerations: Dict[int, int] = settings_manager.get("joint_acceleration", {})

    for axis in HOMING_SEQUENCE:
        try:
            servo = arctos.servos[axis - 1]

            # Compute target zero position with user-defined offset
            user_offset = offsets.get(axis - 1, 0)
            base_zero = ZERO_POSITIONS.get(axis, 0)
            target_zero = base_zero + user_offset

            # Retrieve speed and acceleration settings (with defaults)
            speed = speeds.get(axis - 1, 500)
            accel = accelerations.get(axis - 1, 150)

            logger.info(
                f"Homing axis {axis}: base_zero={base_zero}, offset={user_offset}, "
                f"speed={speed}, accel={accel}"
            )

            # 1) Move to home switch
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()

            # 2) Move to zero position (+ offset)
            raw_target = target_zero * 100  # convert to servo raw units
            servo.run_motor_absolute_motion_by_axis(speed, accel, raw_target)
            arctos.wait_for_motors_to_stop()

            # 3) Align software with hardware reference
            servo.set_current_axis_to_zero()
            logger.info(f"Axis {axis} homed successfully")

        except Exception as e:
            logger.error(f"Error homing axis {axis}: {e}", exc_info=True)

    logger.info("All axes have been homed.")


def move_to_sleep_pose(arctos: Any, settings_manager: SettingsManager) -> None:
    """
    Move all axes to a safe sleep pose in reverse order (joint 6 to 1):
    1. Move to the home switch via built-in b_go_home().
    2. Move to the predefined sleep position.

    Args:
        arctos: Robot controller instance.
        settings_manager: SettingsManager instance for speed/accel settings.

    Returns:
        None
    """
    logger.info("Moving to sleep pose for all axes (6->1)")

    # Retrieve settings for speeds and accelerations
    speeds: Dict[int, int] = settings_manager.get("joint_speeds", {})
    accelerations: Dict[int, int] = settings_manager.get("joint_acceleration", {})

    for axis in HOMING_SEQUENCE:
        try:
            servo = arctos.servos[axis - 1]

            # Retrieve sleep position (raw units)
            sleep_pos = SLEEP_POSITIONS.get(axis, 0)
            speed = speeds.get(axis - 1, 500)
            accel = accelerations.get(axis - 1, 150)

            logger.info(
                f"Axis {axis}: moving to sleep_pos={sleep_pos}, speed={speed}, accel={accel}"
            )

            # 1) Move to home switch
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()

            # 2) Move to sleep position
            raw_target = sleep_pos * 100  # convert to servo raw units
            servo.run_motor_absolute_motion_by_axis(speed, accel, raw_target)
            arctos.wait_for_motors_to_stop()

            logger.info(f"Axis {axis} moved to sleep position")

        except Exception as e:
            logger.error(f"Error moving axis {axis} to sleep pose: {e}", exc_info=True)

    logger.info("All axes have reached sleep pose.")
