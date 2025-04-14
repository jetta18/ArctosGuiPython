import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import os
from robomeshcat import Object

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PathPlanner:
    def __init__(self, filename: str = None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
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
        try:
            return sorted([f for f in os.listdir(self.programs_dir) if f.endswith('.json')])
        except Exception as e:
            logger.debug(f"⚠️ Error listing programs: {e}")
            return []

    def capture_pose(self, robot) -> None:
        current_pose = robot.get_current_joint_angles()
        cartesian_coords = robot.ee_position

        self.poses.append({
            "joints": current_pose.tolist(),
            "cartesian": cartesian_coords.tolist()
        })

        logger.debug(f"✅ Saved Pose: {self.poses[-1]}")
        self.visualize_saved_poses(robot)

    def delete_pose(self, index: int, robot) -> None:
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

    def load_program(self, program_name: Optional[str] = None) -> Tuple[bool, str]:
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
                sphere = Object.create_sphere(radius=0.02, name=f"pose_{idx+1}", color=[0, 0, 1], opacity=0.7)
                sphere.pos = cartesian
                robot.scene.add_object(sphere)
                self.visualized_objects[idx] = sphere
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Visualisieren von Pose {idx + 1}: {e}")
