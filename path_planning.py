import json
import os
import time
import rospy
from std_msgs.msg import String
import move_can

class PathPlanner:
    """
    PathPlanner is responsible for recording, saving, loading, and executing predefined joint poses
    for a robotic arm using MoveIt! and ROS.
    """
    
    def __init__(self, filename: str = "path_program.json"):
        """
        Initializes the PathPlanner.
        
        :param filename: The filename for saving and loading stored joint positions.
        """
        self.poses = []  # List to store recorded joint angles
        self.filename = filename  # File for JSON storage
        
        # ROS publisher for sending UI commands (e.g., moving to joint positions)
        self.ui_command_pub = rospy.Publisher('/ui_command', String, queue_size=10)
    
    def capture_pose(self, joint_state_msg) -> None:
        """
        Stores the current joint position as a new pose.
        
        :param joint_state_msg: ROS message containing the current joint positions.
        """
        joint_positions = list(joint_state_msg.position)  # Convert tuple to list
        self.poses.append(joint_positions)  # Append joint positions to stored poses
        print(f"Pose saved: {joint_positions}")
    
    def save_program(self) -> None:
        """
        Saves the recorded joint poses into a JSON file.
        """
        with open(self.filename, "w") as file:
            json.dump(self.poses, file, indent=4)
        print(f"Program saved as {self.filename}")
    
    def load_program(self) -> None:
        """
        Loads a previously saved set of joint poses from a JSON file.
        """
        try:
            with open(self.filename, "r") as file:
                self.poses = json.load(file)  # Load stored joint poses into memory
            print(f"Program loaded: {self.filename}")
        except FileNotFoundError:
            print("No saved programs found!")
    
    def execute_path(self, Arctos) -> None:
        """
        Sends stored joint poses to MoveIt! for execution.
        
        :param Arctos: An instance of the robot controller used for movement execution.
        """
        if not self.poses:
            print("No stored program available!")
            return

        for idx, pose in enumerate(self.poses):
            print(f"Sending Pose {idx + 1} to MoveIt: {pose}")
            
            valid_pose = pose[:6]  # Ensure only 6 values are sent (robot's joint limits)
            msg = "go_to_joint_state," + ','.join(map(str, valid_pose))
            
            print(f"DEBUG: Sending message: {msg}")  # Debugging output
            self.ui_command_pub.publish(msg)  # Send command to ROS topic
            
            rospy.sleep(3)  # Allow MoveIt! time to execute the movement
            
            # Retrieve the current joint positions after the movement
            joint_positions_rad = move_can.get_joint_states()
            
            if joint_positions_rad is None:
                rospy.logwarn("Error: No valid joint positions received.")
                return  # Abort execution if no data received
            
            # Move the robot to the received joint positions
            Arctos.move_to_angles(joint_positions_rad)
            
            # Wait until the motors stop before proceeding to the next pose
            move_can.wait_for_motors_to_stop(Arctos)
