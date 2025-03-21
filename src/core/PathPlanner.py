import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import os
from nicegui import ui
from meshcat.geometry import Sphere
from meshcat.transformations import translation_matrix


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  

class PathPlanner:
    """
    PathPlanner is responsible for recording, saving, loading, and executing predefined joint poses
    for a robotic arm using Pinocchio.
    """

    def __init__(self, filename: str = None):
        """
        Initializes the PathPlanner.

        :param filename: The filename for saving and loading stored joint positions.
        """
        # Get the absolute path to the programs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.programs_dir = os.path.join(current_dir, '..', 'programs')
        os.makedirs(self.programs_dir, exist_ok=True)  # Create programs dir if it doesn't exist
        
        # Default filename if none provided
        if filename is None:
            filename = "default_program.json"
        
        self.filename = filename
        self.current_program_path = os.path.join(self.programs_dir, self.filename)
        self.poses: List[Dict[str, List[float]]] = []  # List to store recorded joint angles
        self.load_program()
    
    def get_available_programs(self) -> List[str]:
        """
        Returns a list of available program filenames in the programs directory.
        
        :return: List of program filenames
        """
        try:
            # Get all .json files in the programs directory
            programs = [f for f in os.listdir(self.programs_dir) if f.endswith('.json')]
            return sorted(programs)
        except Exception as e:
            logger.debug(f"⚠️ Error listing programs: {e}")
            return []

    def capture_pose(self, robot) -> None:
        """
        Saves the current robot pose, including joint angles and Cartesian coordinates, 
        and immediately visualizes it in MeshCat.

        :param robot: The robot instance that provides the current joint angles and end-effector position.
        :type robot: ArctosPinocchioRobot (or equivalent class)
        """
        # Retrieve current joint angles
        current_pose = robot.get_current_joint_angles()

        # Retrieve the Cartesian position of the end-effector
        cartesian_coords = robot.ee_position  # X, Y, Z coordinates

        # Store the pose as a dictionary containing joint angles and Cartesian coordinates
        self.poses.append({
            "joints": current_pose.tolist(),
            "cartesian": cartesian_coords.tolist()
        })

        logger.debug(f"✅ Saved Pose: {self.poses[-1]}")

        # Immediately visualize the newly saved pose in MeshCat
        self.visualize_saved_poses(robot)

    def delete_pose(self, index: int, robot) -> None:
        """
        Deletes a stored pose and removes its corresponding visualization from MeshCat.

        :param index: The index of the pose to be deleted.
        :type index: int
        :param robot: The robot instance that contains the MeshCat viewer.
        :type robot: ArctosPinocchioRobot (or equivalent class)
        """
        if 0 <= index < len(self.poses):
            # Remove the pose from the list
            deleted_pose = self.poses.pop(index)
            logger.debug(f"🗑️ Pose {index + 1} deleted: {deleted_pose}")

            # Define the MeshCat path for the corresponding sphere
            meshcat_path = f"pose_{index + 1}"

            try:
                # Delete the object in MeshCat
                robot.viz.viewer[meshcat_path].delete()
                logger.debug(f"🔴 Sphere {meshcat_path} removed from MeshCat.")
            except Exception as e:
                logger.debug(f"⚠️ Error while deleting MeshCat sphere {meshcat_path}: {e}")


            # Update the remaining visualized spheres in MeshCat
            self.visualize_saved_poses(robot)

    def save_program(self, program_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Saves the recorded joint poses into a JSON file with the given name.
        
        :param program_name: Optional name for the program file (without extension)
        :return: Tuple of (success, message)
        """
        try:
            if program_name:
                # Ensure the name has .json extension
                if not program_name.endswith('.json'):
                    program_name += '.json'
                self.filename = program_name
                self.current_program_path = os.path.join(self.programs_dir, self.filename)
            
            with open(self.current_program_path, "w") as file:
                json.dump(self.poses, file, indent=4)
            
            logger.debug(f"✅ Program saved as {self.current_program_path}")
            return True, f"Program saved as {self.filename}"
        except Exception as e:
            error_msg = f"⚠️ Error saving program: {e}"
            logger.debug(error_msg)
            return False, error_msg

    def load_program(self, program_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Loads a previously saved set of joint poses from a JSON file and ensures correct formatting.
        
        :param program_name: Optional name of the program file to load (without extension)
        :return: Tuple of (success, message)
        """
        try:
            if program_name:
                # Ensure the name has .json extension
                if not program_name.endswith('.json'):
                    program_name += '.json'
                self.filename = program_name
                self.current_program_path = os.path.join(self.programs_dir, self.filename)
            
            with open(self.current_program_path, "r") as file:
                data = json.load(file)  # Load stored joint poses

                # Ensure the loaded data is a list of dictionaries
                if isinstance(data, list) and all(isinstance(pose, dict) for pose in data):
                    self.poses = data
                    logger.debug(f"✅ Program loaded: {self.current_program_path}")
                    return True, f"Program {self.filename} loaded successfully"
                else:
                    error_msg = f"❌ Invalid format in {self.current_program_path}, resetting poses."
                    logger.debug(error_msg)
                    self.poses = []
                    return False, error_msg

        except FileNotFoundError:
            error_msg = f"⚠️ Program {self.filename} not found!"
            logger.debug(error_msg)
            self.poses = []
            return False, error_msg
        except json.JSONDecodeError:
            error_msg = f"❌ Error: JSON file {self.filename} is corrupted, resetting poses."
            logger.debug(error_msg)
            self.poses = []
            return False, error_msg

    def execute_path(self, robot, Arctos) -> None:
        """
        Moves the robot through the recorded poses using Pinocchio visualization.

        :param robot: The robot instance (ArctosPinocchioRobot).
        :param sleep_time: The delay between executing poses (in seconds).
        """
        if not self.poses:
            logger.debug("⚠️ No stored program available!")
            return

        for idx, pose in enumerate(self.poses):
            try:
                # Extrahiere die Gelenkwinkel aus dem Dictionary
                joint_angles = np.array(pose["joints"])

                # Prüfe, ob die Länge der Gelenkwinkel zu klein ist (z. B. nur 6 statt 8)
                if len(joint_angles) < robot.model.nq:
                    missing_joints = robot.model.nq - len(joint_angles)  # Anzahl fehlender Werte
                    joint_angles = np.concatenate((joint_angles, np.zeros(missing_joints)))  # Ergänze 0-Werte

                logger.debug(f"🔹 Executing Pose {idx + 1}: {np.degrees(joint_angles)} (degrees)")

                # Check if the pose respects joint limits
                if not robot.check_joint_limits(joint_angles):
                    logger.debug("❌ Error: Pose exceeds joint limits. Skipping...")
                    continue  # Skip invalid poses

                # Move the robot to the pose
                robot.set_joint_angles_animated(joint_angles)  # Visualize movement
                joint_positions_rad = robot.get_current_joint_angles()
                if joint_positions_rad is None:
                    ui.notify("❌ No valid joint positions received!", color='red')
                    return
                #arctos.wait_for_motors_to_stop()
                Arctos.move_to_angles(joint_positions_rad)
                Arctos.wait_for_motors_to_stop()
                #time.sleep(2)  # Wait before moving to the next pose

            except KeyError as e:
                logger.debug(f"⚠️ Missing data in pose {idx}: {e}")
            except Exception as e:
                logger.debug(f"⚠️ Unexpected error while executing pose {idx}: {e}")

        logger.debug("✅ Path execution completed!")

    def visualize_saved_poses(self, robot) -> None:
        """
        Visualizes all stored end-effector positions in MeshCat as small spheres.

        :param robot: The robot instance that contains the MeshCat viewer.
        :type robot: ArctosPinocchioRobot (or equivalent class)
        """
        if not self.poses:
            logger.debug("⚠️ No stored poses to visualize!")
            return

        logger.debug(f"🔵 Visualizing {len(self.poses)} saved poses...")

        for idx, pose in enumerate(self.poses):
            try:
                # Extract stored Cartesian coordinates
                cartesian_coords = np.array(pose["cartesian"])
                logger.debug(f"🟠 Visualizing Pose {idx + 1} at Position {cartesian_coords}")

                # Create a small sphere to represent the pose in MeshCat
                sphere = Sphere(0.02)  # Radius = 2 cm
                transform = translation_matrix(cartesian_coords)  # Set position of the sphere

                # Define the MeshCat path for this sphere
                meshcat_name = f"pose_{idx + 1}"

                # Add the sphere to MeshCat
                robot.viz.viewer[meshcat_name].set_object(sphere)
                robot.viz.viewer[meshcat_name].set_property("material.color", [0, 0, 1])  # Set color to blue
                robot.viz.viewer[meshcat_name].set_transform(transform)
            except Exception as e:
                logger.debug(f"⚠️ Error visualizing pose {idx}: {e}")
