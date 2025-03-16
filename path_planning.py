import json
import os
import time
import numpy as np
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  

class PathPlanner:
    """
    PathPlanner is responsible for recording, saving, loading, and executing predefined joint poses
    for a robotic arm using Pinocchio.
    """

    def __init__(self, filename: str = "path_program.json"):
        """
        Initializes the PathPlanner.

        :param filename: The filename for saving and loading stored joint positions.
        """
        self.poses = []  # List to store recorded joint angles
        self.filename = filename  # File for JSON storage

    def capture_pose(self, robot) -> None:
        """
        Stores the current robot joint angles as a new pose.

        :param robot: The robot instance from ui.py (ArctosPinocchioRobot)
        """
        current_pose = robot.get_current_joint_angles()  # Get current joint angles
        self.poses.append(current_pose.tolist())  # Convert numpy array to list
        logger.debug(f"✅ Pose saved: {np.degrees(current_pose)} (degrees)")

    def save_program(self) -> None:
        """
        Saves the recorded joint poses into a JSON file.
        """
        with open(self.filename, "w") as file:
            json.dump(self.poses, file, indent=4)
        logger.debug(f"✅ Program saved as {self.filename}")

    def load_program(self) -> None:
        """
        Loads a previously saved set of joint poses from a JSON file.
        """
        try:
            with open(self.filename, "r") as file:
                self.poses = json.load(file)  # Load stored joint poses into memory
            logger.debug(f"✅ Program loaded: {self.filename}")
        except FileNotFoundError:
            logger.debug("⚠️ No saved programs found!")

    def execute_path(self, robot, sleep_time: float = 2.0) -> None:
        """
        Moves the robot through the recorded poses using Pinocchio visualization.

        :param robot: The robot instance (ArctosPinocchioRobot) from ui.py.
        :param sleep_time: The delay between executing poses (in seconds).
        """
        if not self.poses:
            logger.debug("⚠️ No stored program available!")
            return

        for idx, pose in enumerate(self.poses):
            pose_np = np.array(pose)  # Convert list to numpy array
            logger.debug(f"🔹 Executing Pose {idx + 1}: {np.degrees(pose_np)} (degrees)")

            # Check if the pose respects joint limits
            if not robot.check_joint_limits(pose_np):
                logger.debug("❌ Error: Pose exceeds joint limits. Skipping...")
                continue  # Skip invalid poses

            # Move the robot to the pose
            robot.q = pose_np  # Update internal state
            robot.display()  # Visualize movement
            time.sleep(sleep_time)  # Wait before moving to the next pose

        logger.debug("✅ Path execution completed!")
