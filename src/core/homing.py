"""
This module provides functionalities for homing and moving the Arctos robot to specific poses.

It includes functions for moving the robot's motors to their zero positions (homing process)
and to a sleep position (a safe resting state).
"""
import time

# Define motor IDs and their respective zero positions (home positions)
MOTOR_IDS = [3, 2, 1]  # Motor IDs 4
ZERO_POSITIONS = [-2410, -3300, -1038]  # 1700 Zero positions (TODO: Convert to radians, e.g., [-0.616, 0, 0])


def move_to_zero_pose(Arctos) -> None:
    """
    Moves the motors to their zero positions (homing process).

    This function sequentially moves each motor to its home position (using the built in go home
    functionality) and then to a defined zero position. After reaching the zero position, the
    current axis position is set to zero, aligning the software and hardware reference frames.

    Args:
        Arctos: Instance of the robot controller managing the servos.

    Returns:
        None

    """
    print("Starting homing process for motors...")

    # Move each motor to its home position and then to its defined zero position
    for motor_id, zero_position in zip(MOTOR_IDS, ZERO_POSITIONS):
        # Move motor to home position
        Arctos.servos[motor_id - 1].b_go_home()

        # Move motor to its zero position with specified speed and acceleration.
        # Multiply zero position by 100, because the motor takes values like 100000 for 1000
        Arctos.servos[motor_id - 1].run_motor_absolute_motion_by_axis(500, 70, zero_position * 100)

        # Wait for the motors to stop moving.
        Arctos.wait_for_motors_to_stop()

        # Set the current axis position to zero,
        # so that the software and hardware are aligned
        Arctos.servos[motor_id - 1].set_current_axis_to_zero()

    print("All motors have reached their zero positions.")


def move_to_sleep_pose(Arctos) -> None:
    """
    Moves the robot into a sleep position (safe resting state).

    This function brings the motors to predefined sleep positions, often to prevent damage when the robot is not in use.

    Args:
        Arctos: Instance of the robot controller managing the servos.

    Returns:
        None
    """
    print("Starting movement to sleep position...")

    ##### TODO: Implement sleep pose for other motors #####

    # Move specific motors to home positions (additional movements might be required)
    Arctos.servos[2].b_go_home()
    Arctos.servos[1].b_go_home()

    print("All motors have reached their sleep positions.")