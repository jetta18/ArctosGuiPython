import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import os
from robomeshcat import Object
import meshcat.geometry as g
import meshcat.transformations as tf

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PathPlanner:
    """
    A class for managing and executing robot motion paths.

    This class handles the loading, saving, and execution of programs, which consist of a sequence of robot poses.
    It also manages visualization of the saved poses using RoboMeshCat.
    """

    def __init__(self, filename: str = None):
        """
        Initializes the PathPlanner.

        Args:
            filename (str, optional): The filename of the program to load. Defaults to "default_program.json".
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
        # Construct the path to the programs directory
        self.programs_dir = os.path.join(current_dir, '..', 'programs')
        os.makedirs(self.programs_dir, exist_ok=True)

        if filename is None:
            filename = "default_program.json"

        self.filename = filename
        self.current_program_path = os.path.join(self.programs_dir, self.filename)
        self.poses: List[Dict[str, List[float]]] = []
        self.visualized_objects: Dict[int, Object] = {}  # Für RoboMeshCat-Sphären
        self.load_program()

    def get_available_programs(self) -> List[str]:
        """
        Retrieves a list of available programs in the programs directory.

        Returns:
            List[str]: A sorted list of program filenames (with .json extension) in the programs directory.
                       Returns an empty list if an error occurs while listing programs.

        Raises:
        """
        try:
            return sorted([f for f in os.listdir(self.programs_dir) if f.endswith('.json')])
        except Exception as e:
            logger.debug(f"⚠️ Error listing programs: {e}")
            return []

    def capture_pose(self, robot) -> None:
        """
        Captures the current pose of the robot and appends it to the program.

        Args:
            robot: An instance of the ArctosPinocchioRobot class representing the robot.

        Raises:
            TypeError: if robot is not type ArctosPinocchioRobot
        
        """
        current_pose = robot.get_current_joint_angles()
        cartesian_coords = robot.ee_position

        self.poses.append({
            "joints": current_pose.tolist(),
            "cartesian": cartesian_coords.tolist()
        })

        logger.debug(f"✅ Saved Pose: {self.poses[-1]}")
        self.visualize_saved_poses(robot)

    def delete_pose(self, index: int, robot) -> None:
        """
        Deletes a pose from the program at the specified index.

        Args:
            index (int): The index of the pose to delete.
            robot: An instance of the ArctosPinocchioRobot class representing the robot.

        Raises:
            ValueError: If the index is out of range.
            TypeError: if robot is not type ArctosPinocchioRobot
            IndexError: If the index is out of bounds for the list of poses.

        """
        if 0 <= index < len(self.poses):
            deleted_pose = self.poses.pop(index)
            logger.debug(f"🗑️ Pose {index + 1} gelöscht: {deleted_pose}")

            if index in self.visualized_objects:
                try:
                    robot.scene.remove_object(self.visualized_objects[index])
                    del self.visualized_objects[index]
                except Exception as e:
                    logger.debug(f"⚠️ Fehler beim Entfernen der Visualisierung: {e}")

            self.visualize_saved_poses(robot)

    def save_program(self, program_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Saves the current program to a JSON file.

        Args:
            program_name (Optional[str]): The name of the program to save. If None, the currently loaded filename is used.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure and a message.

        Raises:
            TypeError: if program name is not type str
            
        """
        try:
            if program_name:
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

    def load_program(self, program_name: Optional[str] = None, robot=None) -> Tuple[bool, str]:
        """
        Loads a program from a JSON file and visualizes the poses if a robot instance is provided.

        Args:
            program_name (Optional[str]): The name of the program to load. If None, the currently loaded filename is used.
            robot: Optional instance of the ArctosPinocchioRobot to visualize the loaded poses.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure and a status message.
        """
        try:
            if program_name:
                if not program_name.endswith('.json'):
                    program_name += '.json'
                self.filename = program_name
                self.current_program_path = os.path.join(self.programs_dir, self.filename)

            with open(self.current_program_path, "r") as file:
                data = json.load(file)
                if isinstance(data, list) and all(isinstance(pose, dict) for pose in data):
                    self.poses = data
                    logger.debug(f"✅ Program loaded: {self.current_program_path}")

                    if robot is not None:
                        self.visualize_saved_poses(robot)

                    return True, f"Program {self.filename} loaded successfully"
                else:
                    self.poses = []
                    return False, f"❌ Invalid format in {self.filename}, poses cleared."

        except FileNotFoundError:
            self.poses = []
            return False, f"⚠️ Program {self.filename} not found!"
        except json.JSONDecodeError:
            self.poses = []
            return False, f"❌ JSON file {self.filename} is corrupted, poses cleared."


    def execute_path(self, robot, Arctos) -> None:
        """
        Executes the loaded program by moving the robot through the stored poses.

        Args:
            robot: An instance of the ArctosPinocchioRobot class representing the robot.
            Arctos: An instance of the ArctosController class for communicating with the actual robot hardware.

        Raises:
            TypeError: if robot is not type ArctosPinocchioRobot or Arctos is not type ArctosController
            ValueError: If the joint configuration in a pose exceeds the robot's joint limits.
        """

        if not self.poses:
            logger.debug("⚠️ No stored program available!")
            return

        for idx, pose in enumerate(self.poses):
            try:
                joint_angles = np.array(pose["joints"])
                if len(joint_angles) < robot.model.nq:
                    missing = robot.model.nq - len(joint_angles)
                    joint_angles = np.concatenate((joint_angles, np.zeros(missing)))

                logger.debug(f"🔹 Executing Pose {idx + 1}: {np.degrees(joint_angles)}")

                if not robot.check_joint_limits(joint_angles):
                    logger.debug("❌ Pose überschreitet Gelenkgrenzen. Übersprungen.")
                    continue

                robot.set_joint_angles_animated(joint_angles)
                joint_positions_rad = robot.get_current_joint_angles()
                if joint_positions_rad is None:
                    return

                Arctos.move_to_angles(joint_positions_rad)
                Arctos.wait_for_motors_to_stop()

            except Exception as e:
                logger.debug(f"⚠️ Fehler bei Pose {idx + 1}: {e}")

        logger.debug("✅ Path execution completed!")

    def visualize_saved_poses(self, robot) -> None:
        """
        Visualizes the saved poses in the RoboMeshCat scene.

        Args:
            robot: An instance of the ArctosPinocchioRobot class representing the robot.

        Raises:
            TypeError: if robot is not type ArctosPinocchioRobot
        """
        # Bestehende löschen
        for obj in self.visualized_objects.values():
            try:
                robot.scene.remove_object(obj)
            except Exception:
                pass
        self.visualized_objects.clear()

        for idx, pose in enumerate(self.poses):
            try:
                cartesian = np.array(pose["cartesian"])
                rounded = np.round(cartesian, 3)

                # Farbverlauf berechnen (grün → rot)
                t = idx / max(1, len(self.poses) - 1)
                color = [round(1.0 * t, 2), round(1.0 - t, 2), 0.0]  # [r, g, b]

                # Name zusammensetzen mit Index, Position und Farbe
                name = f"Pose {idx+1} | x={rounded[0]} y={rounded[1]} z={rounded[2]} | color={color}"

                # Kugel erstellen
                sphere = Object.create_sphere(
                    radius=0.02,
                    name=name,
                    color=color,
                    opacity=0.8
                )
                robot.scene.add_object(sphere)
                sphere.pos = cartesian
                self.visualized_objects[idx] = sphere

            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Visualisieren von Pose {idx + 1}: {e}")

