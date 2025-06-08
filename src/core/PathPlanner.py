import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import os
from robomeshcat import Object

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
        self.visualized_objects: Dict[int, Object] = {}  # For RoboMeshCat spheres
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


    def execute_path(
            self,
            robot,
            arctos,
            speeds: list[int] | int = 500,
            acceleration: list[int] | int = 150,
    ) -> None:
        """
        Play the stored pose list on the physical robot.

        Parameters
        ----------
        robot : ArctosPinocchioRobot
        arctos : ArctosController
        speeds : int | list[int]
            Either one global RPM value **or** a list of six values
            (one per joint).  Defaults to 500 RPM.
        acceleration : int
            Global acceleration (0‑255).  Defaults to 150.
        """
        if not self.poses:
            logger.warning("⚠️  No stored program.")
            return

        # --- build 6‑element speed list --------------------------------------
        if isinstance(speeds, int):
            speed_list = [max(0, min(speeds, 3000))] * 6
        else:
            if len(speeds) != 6:
                raise ValueError("speeds must have length 6")
            speed_list = [max(0, min(s, 3000)) for s in speeds]

        # --- build 6‑element acceleration list ------------------------------
        if isinstance(acceleration, int):
            acceleration_list = [max(0, min(acceleration, 255))] * 6
        else:
            if len(acceleration) != 6:
                raise ValueError("acceleration must have length 6")
            acceleration_list = [max(0, min(a, 255)) for a in acceleration]

        for idx, pose in enumerate(self.poses):
            try:
                q = np.asarray(pose["joints"])
                if len(q) < robot.model.nq:
                    missing = robot.model.nq - len(q)
                    q = np.concatenate((q, np.zeros(missing)))

                logger.debug("🔹 Executing Pose %d: %s", idx + 1, np.degrees(q))

                if not robot.check_joint_limits(q):
                    logger.warning("Pose %d violates limits – skipped.", idx + 1)
                    continue

                # twin animation
                robot.set_joint_angles_animated(q, duration=1.0, steps=15)
                joint_positions_rad = robot.get_current_joint_angles()
                if joint_positions_rad is None:
                    return
                angles_rad = q.tolist()[:6]

                # physical move
                arctos.move_to_angles(angles_rad, speeds=speed_list, acceleration=acceleration_list)
                arctos.wait_for_motors_to_stop()

            except Exception as e:
                logger.error("Pose %d failed: %s", idx + 1, e)

        logger.info("✅ Path execution completed")


    def visualize_saved_poses(self, robot) -> None:
        """
        Visualizes the saved poses in the RoboMeshCat scene.

        Args:
            robot: An instance of the ArctosPinocchioRobot class representing the robot.

        Raises:
            TypeError: if robot is not type ArctosPinocchioRobot
        """
        # Remove existing
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

                # Create sphere
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
                logger.warning(f"⚠️ Error visualizing pose {idx + 1}: {e}")

