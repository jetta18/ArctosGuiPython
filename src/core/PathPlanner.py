import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import os
from nicegui import ui
from meshcat.geometry import Sphere
from meshcat.transformations import translation_matrix


# Set up logging for the PathPlanner module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PathPlanner:
    """Manages the recording, saving, loading, and execution of predefined joint poses for a robotic arm.

    This class handles the storage and retrieval of robot poses, which are used to define paths for
    the robot to follow. It interfaces with the ArctosPinocchioRobot class to capture and visualize
    robot poses.
    """

    def __init__(self, filename: str = None):
        """Initializes the PathPlanner with an optional filename for storing and loading joint positions.

        Args:
            filename (str, optional): The filename for saving and loading stored joint positions.
            If None, defaults to "default_program.json". Defaults to None.

        The constructor performs the following operations:
        - Determines the directory for storing programs.
        - Creates the directory if it does not exist.
        - Sets the filename and the full path for the program file.
        - Initializes an empty list to store poses.
        - Loads a program from the specified file if it exists.
        """
        # Get the absolute path to the programs directory, located two levels up and in 'programs'
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
        """Retrieves a sorted list of available program filenames in the programs directory.

        This method lists all files ending with '.json' in the programs directory,
        sorts them alphabetically, and returns the sorted list.
        
        Returns:
            List[str]: A sorted list of program filenames.
            If an error occurs while listing the programs, returns an empty list.
        """
        try:
            # Get all .json files in the programs directory and sort them
            # Get all .json files in the programs directory
            programs = [f for f in os.listdir(self.programs_dir) if f.endswith('.json')]
            return sorted(programs)
        except Exception as e:
            logger.debug(f"⚠️ Error listing programs: {e}")
            return []

    def capture_pose(self, robot) -> None:
        """Captures and stores the current robot pose, including joint angles and Cartesian coordinates.

        This method gets the current joint angles and the end-effector Cartesian position
        from the robot instance, stores them in the `self.poses` list, and visualizes the
        pose in MeshCat immediately.

        Args:
            robot (ArctosPinocchioRobot): The robot instance that provides the current joint angles
                and end-effector position.
        """
        # Retrieve current joint angles
        # Retrieve current joint angles and cartesian coordinates from the robot
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
        """Deletes a stored pose and removes its visualization from MeshCat.

        Args:
            index (int): The index of the pose to be deleted (0-based).
            robot (ArctosPinocchioRobot): The robot instance that contains the MeshCat viewer.

        The method does the following:
        - Removes the pose from the list of stored poses.
        - Deletes the corresponding sphere in MeshCat.
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
        """Saves the recorded joint poses into a JSON file.
        
        This method saves the current set of stored joint poses (`self.poses`) into a JSON file.
        If a program_name is provided, it will save the poses to that file. Otherwise, it will
        use the current filename.

        Args:
            program_name (str, optional): Optional name for the program file (without extension).
            If provided, it will override the current filename. Defaults to None.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure, and a message string.
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
        """Loads a previously saved set of joint poses from a JSON file.
        
        This method attempts to load joint poses from a JSON file. If the program_name is provided,
        it will load from that file. Otherwise, it will use the current filename. It also checks
        if the loaded data has the correct format.

        Args:
            program_name (str, optional): Optional name of the program file to load (without extension).
                If provided, it will override the current filename. Defaults to None.
        
        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure, and a message string.
        """
        # Check if a custom program name is provided
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
        """Executes a path by moving the robot through the recorded poses.

        This method iterates through the stored poses in `self.poses` and moves the robot
        to each pose sequentially. It uses the robot's visualization capabilities to animate
        the movement and the Arctos controller to move the real robot.

        Args:
            robot (ArctosPinocchioRobot): The robot instance.
            Arctos (ArctosController): The instance of the Arctos controller

        The method does the following:
        - Verifies that there are stored poses to execute.
        - Iterates through each pose.
        - Moves the robot to the pose.
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
        """Visualizes all stored end-effector positions in MeshCat as small spheres.

        This method iterates through all stored poses in `self.poses`, extracts the Cartesian
        coordinates of the end-effector, and visualizes them as spheres in MeshCat.

        Args:
            robot (ArctosPinocchioRobot): The robot instance that contains the MeshCat viewer.
        
        The method does the following:
        - Verifies that there are stored poses to visualize.
        - Iterates through each stored pose.
        - Visualizes the end-effector position as a sphere in MeshCat.
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
