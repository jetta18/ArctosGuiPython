"""
File: core/homing.py

This module provides functions to home the robot axes and move them into a safe sleep pose.
Homing zero positions are entirely determined by offsets saved in settings (no hardcoded base zeros).
"""
import logging
from typing import Any, Dict
import time

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
            axis_id = axis - 1  # 0-based index for servos

            # Get the user-specified offset (default to 0 if not set)
            user_offset = offsets.get(axis_id, 0)
            
            # Get speed and acceleration with defaults
            speed = speeds.get(axis_id, 500)
            accel = accelerations.get(axis_id, 150)

            logger.info(
                f"Homing axis {axis}: offset={user_offset}, speed={speed}, accel={accel}"
            )

            # 1) Home the motor (this resets the encoder to 0)
            logger.debug(f"Axis {axis}: Moving to home switch...")
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()
            
            # Small delay to ensure motor has stopped completely
            time.sleep(0.1)
            
            # 2) Move to the user-specified offset position
            if user_offset != 0:
                logger.debug(f"Axis {axis}: Moving to offset position {user_offset}...")
                # Use relative motion from the current position (which should be 0 after homing)
                servo.run_motor_relative_motion_by_axis(speed, accel, int(user_offset))
                arctos.wait_for_motors_to_stop()
                time.sleep(0.1)  # Small delay

            # 3) Set the current position as the zero reference
            servo.set_current_axis_to_zero()
            logger.info(f"Axis {axis} homed successfully at offset {user_offset}")

        except Exception as e:
            logger.error(f"Error homing axis {axis}: {e}", exc_info=True)
            raise  # Re-raise to stop the homing process if any axis fails

    logger.info("All axes have been homed using settings offsets.")


def move_to_sleep_pose(arctos: Any, settings_manager: SettingsManager) -> None:
    """
    Move all axes to a safe sleep pose in reverse order (joint 6 to 1):
    - For axes 4-6: Move to home switch and then to zero position offset
    - For axes 1-3: Just move to home switch

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
    offsets = settings_manager.get("homing_offsets", {})

    for axis in HOMING_SEQUENCE:
        try:
            axis_id = axis - 1  # 0-based index
            servo = arctos.servos[axis_id]

            # Get speed and acceleration with defaults
            speed = speeds.get(axis_id, 500)
            accel = accelerations.get(axis_id, 150)

            logger.info(f"Moving axis {axis} to sleep pose...")

            # 1) Move to home switch first (this resets the encoder to 0)
            logger.debug(f"Axis {axis}: Moving to home switch...")
            servo.b_go_home()
            arctos.wait_for_motors_to_stop()
            time.sleep(0.1)  # Small delay

            # 2) For axes 4-6, move to zero position offset
            if axis >= 4:  # Axes 4, 5, 6
                user_offset = offsets.get(axis_id, 0)
                if user_offset != 0:
                    logger.debug(f"Axis {axis}: Moving to zero position offset {user_offset}...")
                    # Use relative motion from home position (which should be 0 after homing)
                    servo.run_motor_relative_motion_by_axis(speed, accel, int(user_offset))
                    arctos.wait_for_motors_to_stop()
                    time.sleep(0.1)  # Small delay

            logger.info(f"Axis {axis} moved to sleep position")

        except Exception as e:
            logger.error(f"Error moving axis {axis} to sleep pose: {e}", exc_info=True)
            raise  # Re-raise to stop the process if any axis fails

    logger.info("All axes have reached sleep pose.")
