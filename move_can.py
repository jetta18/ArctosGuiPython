import rospy
from sensor_msgs.msg import JointState
import time
from typing import List, Union  # Add this import

def get_joint_states() -> Union[List[float], None]:
    """
    Retrieves a single JointState message from the `/joint_states` topic and extracts joint angles.
    
    :return: A list of joint angles in radians [joint1, joint2, joint3, joint4, b_axis, c_axis], or None if the required joints are missing.
    """
    msg = rospy.wait_for_message("/joint_states", JointState)
    try:
        # Extract and round joint positions for specified joints
        joint_positions = [
            msg.position[msg.name.index(joint)]
            for joint in ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        ]
    except ValueError as e:
        rospy.logwarn("Missing joints in JointState message: %s", e)
        return None
    
    # Compute B and C axis values from joint5 and joint6
    b_axis = (joint_positions[5] + joint_positions[4]) 
    c_axis = (joint_positions[4] - joint_positions[5]) 
    
    # Return joint angles in the correct format
    return [joint_positions[0], -joint_positions[1], -joint_positions[2], joint_positions[3], -b_axis, c_axis]

def wait_for_motors_to_stop(Arctos) -> None:
    """
    Waits until all motors stop moving before proceeding.
    
    This function continuously checks if any motor is still running and waits until all motors have stopped before returning.
    
    :param Arctos: Instance of the robot controller containing servo objects.
    """
    while any(servo.is_motor_running() for servo in Arctos.servos):
        rospy.logwarn("Motors are still running. Waiting...")
        time.sleep(0.5)  # Wait before checking again