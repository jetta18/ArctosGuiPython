import time
import move_can

# Define motor IDs and their respective zero positions (home positions)
MOTOR_IDS = [3, 2, 1]  # Motor IDs 4
ZERO_POSITIONS = [-2410, -3300, -1038]  # 1700 Zero positions (TODO: Convert to radians, e.g., [-0.616, 0, 0])

def move_to_zero_pose(Arctos) -> None:
    """
    Moves the motors to their zero positions (homing process).
    
    This function sequentially moves each motor to its home position and then to a defined zero position.
    
    :param Arctos: Instance of the robot controller managing the servos.
    """
    print("Starting homing process for motors...")

    ###### TODO: Implement zero pose for other motors ######

    # Move each motor to its home position and then to its defined zero position
    for motor_id, zero_position in zip(MOTOR_IDS, ZERO_POSITIONS):
        Arctos.servos[motor_id - 1].b_go_home()  # Move motor to home position

        # Move motor to its zero position with specified speed and acceleration
        Arctos.servos[motor_id - 1].run_motor_absolute_motion_by_axis(500, 70, zero_position * 100)
        
        move_can.wait_for_motors_to_stop(Arctos)

        # Set the current axis position to zero
        Arctos.servos[motor_id - 1].set_current_axis_to_zero()

    print("All motors have reached their zero positions.")

def move_to_sleep_pose(Arctos) -> None:
    """
    Moves the robot into a sleep position (safe resting state).
    
    This function brings the motors to predefined sleep positions.
    
    :param Arctos: Instance of the robot controller managing the servos.
    """
    print("Starting movement to sleep position...")

    ##### TODO: Implement sleep pose for other motors #####

    # Move specific motors to home positions (additional movements might be required)
    Arctos.servos[2].b_go_home()
    Arctos.servos[1].b_go_home()

    print("All motors have reached their sleep positions.")