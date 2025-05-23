"""
File: core/homing.py

This module provides functions to home the robot axes and move them into a safe sleep pose.
Homing zero positions are entirely determined by offsets saved in settings (no hardcoded base zeros).
"""
import logging
from typing import Any, Dict

from utils.settings_manager import SettingsManager

# Initialize module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# List of motor axes (1-based indexing corresponds to arctos.servos[axis-1])
MOTOR_IDS = [1, 2, 3, 4, 5, 6]

# Base homing sequence for independent mode (all axes)
BASE_HOMING_SEQUENCE = list(reversed(MOTOR_IDS))

# Homing sequence that will be used (can be modified based on settings)
HOMING_SEQUENCE = list(BASE_HOMING_SEQUENCE)  # Default to all axes

# Predefined sleep positions for each axis (raw units)
# TODO: Set appropriate sleep positions as needed
SLEEP_POSITIONS: Dict[int, int] = {axis: 0 for axis in MOTOR_IDS}


def update_homing_sequence(settings_manager: SettingsManager) -> None:
    """
    Update the HOMING_SEQUENCE based on the current settings.
    If coupled_axis_mode is enabled, only axes 1-4 will be homed.
    """
    global HOMING_SEQUENCE
    coupled_mode = settings_manager.get("coupled_axis_mode", False)
    if coupled_mode:
        HOMING_SEQUENCE = [axis for axis in BASE_HOMING_SEQUENCE if axis <= 4]
        logger.info("Coupled B/C axis mode detected. Homing only axes 1-4.")
    else:
        HOMING_SEQUENCE = list(BASE_HOMING_SEQUENCE)

def move_to_zero_pose(arctos: Any, settings_manager: SettingsManager) -> None:
    """
    Perform the homing routine for all axes in reverse order (joint 6 to 1):
    1. Update the homing sequence based on current settings
    2. Move to the home switch via built-in b_go_home().
    3. Move to the configured zero position (offset) from settings.
    4. Set the current axis position to zero in software.

    Note: In coupled B/C axis mode, only axes 1-4 will be homed.

    Args:
        arctos: Robot controller instance providing servo control methods.
        settings_manager: SettingsManager instance for retrieving homing offsets.

    Returns:
        None
    """
    logger.info("Starting homing process for all axes (6->1) using settings offsets")

    # Update homing sequence based on current settings and get coupled mode status
    update_homing_sequence(settings_manager)
    coupled_mode = settings_manager.get("coupled_axis_mode", False)
    
    # Log warning if in coupled mode
    if coupled_mode:
        logger.warning("Coupled B/C axis mode is enabled. Axes 5 and 6 will not be homed automatically.")
    
    # Initialize homing offsets if not present
    offsets = settings_manager.get("homing_offsets", {})
    if not offsets:
        offsets = {axis: 0 for axis in MOTOR_IDS}
        settings_manager.set("homing_offsets", offsets)
    
    # Get speeds and accelerations
    speeds = settings_manager.get("joint_speeds", {})
    accelerations = settings_manager.get("joint_acceleration", {})

    for axis in HOMING_SEQUENCE:
        try:
            servo = arctos.servos[axis - 1]

            # Determine zero position from stored offset (raw units)
            user_offset = offsets.get(axis - 1, 0)
            target_zero = user_offset

            # Retrieve speed and acceleration settings (with defaults)
            speed = speeds.get(axis - 1, 500)
            accel = accelerations.get(axis - 1, 150)

            logger.info(
                f"Homing axis {axis}: target_zero={target_zero}, speed={speed}, accel={accel}"
            )

            # 1) Move to home switch (resets encoder to zero)
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()

            # 2) Move to desired zero position (offset)
            raw_target = target_zero * 100  # convert to servo raw units
            servo.run_motor_absolute_motion_by_axis(speed, accel, raw_target)
            arctos.wait_for_motors_to_stop()

            # 3) Align software reference to current hardware position
            servo.set_current_axis_to_zero()
            logger.info(f"Axis {axis} homed successfully at offset {target_zero}")

        except Exception as e:
            logger.error(f"Error homing axis {axis}: {e}", exc_info=True)

    logger.info("All axes have been homed using settings offsets.")


def move_to_sleep_pose(arctos: Any, settings_manager: SettingsManager) -> None:
    """
    Move all axes to a safe sleep pose in reverse order (joint 6 to 1):
    1. Optionally move to home switch via b_go_home().
    2. Move to the predefined sleep position from SLEEP_POSITIONS.

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

            # Move to home switch first to ensure consistent start (optional)
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()

            # Move to sleep position
            raw_target = sleep_pos * 100  # convert to servo raw units
            servo.run_motor_absolute_motion_by_axis(speed, accel, raw_target)
            arctos.wait_for_motors_to_stop()

            logger.info(f"Axis {axis} moved to sleep position {sleep_pos}")

        except Exception as e:
            logger.error(f"Error moving axis {axis} to sleep pose: {e}", exc_info=True)

    logger.info("All axes have reached sleep pose.")
