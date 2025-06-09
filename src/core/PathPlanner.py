import json
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
import os
import time 
from robomeshcat import Object

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PathPlanner:
    """
    A class for managing and executing robot motion programs.

    This class handles the loading, saving, and execution of programs, 
    which consist of a sequence of actions (poses, waits, gripper commands).
    It also manages visualization of the saved pose actions using RoboMeshCat.
    """

    def __init__(self, filename: str = None):
        """
        Initializes the PathPlanner.

        Args:
            filename (str, optional): The filename of the program to load. Defaults to "default_program.json".
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))  
        self.programs_dir = os.path.join(current_dir, '..', 'programs')
        os.makedirs(self.programs_dir, exist_ok=True)

        if filename is None:
            filename = "default_program.json"

        self.filename = filename
        self.current_program_path = os.path.join(self.programs_dir, self.filename)
        self.program: List[Dict[str, Any]] = []  
        self.visualized_objects: Dict[int, Object] = {}  
        self.load_program() 

    def get_available_programs(self) -> List[str]:
        """
        Retrieves a list of available programs in the programs directory.

        Returns:
            List[str]: A sorted list of program filenames (with .json extension).
        """
        try:
            return sorted([f for f in os.listdir(self.programs_dir) if f.endswith('.json')])
        except Exception as e:
            logger.debug(f"⚠️ Error listing programs: {e}")
            return []

    def capture_pose(self, robot) -> None:
        """
        Captures the current pose of the robot and appends it as a 'POSE' action to the program.

        Args:
            robot: An instance of the ArctosPinocchioRobot class.
        """
        current_joint_angles = robot.get_current_joint_angles()
        cartesian_coords = robot.ee_position

        action = {
            "type": "POSE",
            "joints": current_joint_angles.tolist(),
            "cartesian": cartesian_coords.tolist()
        }
        self.program.append(action)
        logger.debug(f"✅ Added Pose Action: {action}")
        self.visualize_program_actions(robot) 

    def add_wait_action(self, duration_ms: int, robot = None) -> None:
        """
        Adds a 'WAIT' action to the program.

        Args:
            duration_ms (int): The duration to wait in milliseconds.
            robot (Optional): Robot instance, used for re-triggering visualization if UI needs update.
        """
        if not isinstance(duration_ms, int) or duration_ms <= 0:
            logger.warning("⚠️ Invalid wait duration. Must be a positive integer (milliseconds).")
            return
        action = {"type": "WAIT", "duration_ms": duration_ms}
        self.program.append(action)
        logger.debug(f"✅ Added Wait Action: {duration_ms} ms")
        if robot: 
            self.visualize_program_actions(robot) 

    def add_gripper_action(self, command: str, robot = None) -> None:
        """
        Adds a 'GRIPPER' action to the program (OPEN or CLOSE).

        Args:
            command (str): The gripper command, either "OPEN" or "CLOSE".
            robot (Optional): Robot instance, used for re-triggering visualization if UI needs update.
        """
        valid_commands = ["OPEN", "CLOSE"]
        cmd_upper = command.upper()
        if cmd_upper not in valid_commands:
            logger.warning(f"⚠️ Invalid gripper command: {command}. Must be one of {valid_commands}.")
            return
        action = {"type": "GRIPPER", "command": cmd_upper}
        self.program.append(action)
        logger.debug(f"✅ Added Gripper Action: {cmd_upper}")
        if robot: 
            self.visualize_program_actions(robot)

    def delete_action(self, index: int, robot) -> None:
        """
        Deletes an action from the program at the specified index.

        Args:
            index (int): The index of the action to delete.
            robot: An instance of the ArctosPinocchioRobot class for visualization updates.
        """
        if 0 <= index < len(self.program):
            deleted_action = self.program.pop(index)
            logger.debug(f"🗑️ Action {index + 1} deleted: {deleted_action}")

            if index in self.visualized_objects:
                try:
                    robot.scene.remove_object(self.visualized_objects[index])
                    del self.visualized_objects[index]
                except Exception as e:
                    logger.debug(f"⚠️ Error removing visualization for deleted action: {e}")
            
            self.visualize_program_actions(robot) 
        else:
            logger.warning(f"⚠️ Invalid index for deleting action: {index}")

    def save_program(self, program_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Saves the current program to a JSON file.

        Args:
            program_name (Optional[str]): The name of the program. If None, uses the current filename.

        Returns:
            Tuple[bool, str]: Success status and a message.
        """
        if program_name:
            if not program_name.endswith(".json"):
                program_name += ".json"
            self.filename = program_name
            self.current_program_path = os.path.join(self.programs_dir, self.filename)

        data_to_save = {"program": self.program}  
        try:
            with open(self.current_program_path, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            logger.info(f"✅ Program '{self.filename}' saved successfully.")
            return True, f"Program '{self.filename}' saved."
        except IOError as e:
            logger.error(f"❌ Error saving program '{self.filename}': {e}")
            return False, f"Error saving program: {e}"
        except Exception as e:
            logger.error(f"❌ Unexpected error saving program '{self.filename}': {e}")
            return False, f"Unexpected error: {e}"

    def load_program(self, program_name: Optional[str] = None, robot=None) -> Tuple[bool, str]:
        """
        Loads a program from a JSON file and visualizes pose actions.

        Args:
            program_name (Optional[str]): The name of the program. If None, uses current filename.
            robot (Optional): Robot instance for visualization.

        Returns:
            Tuple[bool, str]: Success status and a message.
        """
        if program_name:
            if not program_name.endswith(".json"):
                program_name += ".json"
            self.filename = program_name
            self.current_program_path = os.path.join(self.programs_dir, self.filename)

        try:
            if not os.path.exists(self.current_program_path):
                logger.warning(f"⚠️ Program file '{self.filename}' not found. Creating new empty program.")
                self.program = []
                if robot:
                    self.visualize_program_actions(robot) 
                return True, f"Program file '{self.filename}' not found. New program started."

            with open(self.current_program_path, 'r') as f:
                loaded_data = json.load(f)
                if "poses" in loaded_data and "program" not in loaded_data:
                    logger.info(f"📝 Converting old program format for '{self.filename}'.")
                    self.program = [
                        {"type": "POSE", "joints": pose.get("joints"), "cartesian": pose.get("cartesian")}
                        for pose in loaded_data.get("poses", [])
                    ]
                else:
                    self.program = loaded_data.get("program", [])
            
            logger.info(f"✅ Program '{self.filename}' loaded. {len(self.program)} actions.")
            if robot:
                self.visualize_program_actions(robot)
            return True, f"Program '{self.filename}' loaded."
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decoding JSON from '{self.filename}': {e}")
            self.program = []
            if robot:
                self.visualize_program_actions(robot)
            return False, f"Error decoding program file: {e}"
        except Exception as e:
            logger.error(f"❌ Unexpected error loading '{self.filename}': {e}")
            self.program = []
            if robot:
                self.visualize_program_actions(robot)
            return False, f"Unexpected error: {e}"

    def execute_program( 
            self,
            robot,
            arctos, 
            speeds: list[int] | int = 500,
            acceleration: list[int] | int = 150,
    ) -> None:
        """
        Executes the stored program sequence on the robot.

        Parameters:
            robot : ArctosPinocchioRobot instance for kinematics and simulation.
            arctos : ArctosController instance for physical robot control.
            speeds : Global or per-joint speed (RPM).
            acceleration : Global acceleration (0-255).
        """
        if not self.program:
            logger.warning("⚠️ No program loaded or program is empty.")
            return

        if isinstance(speeds, int):
            speed_list = [max(0, min(speeds, 3000))] * 6
        else:
            if len(speeds) != 6:
                raise ValueError("speeds must have length 6")
            speed_list = [max(0, min(s, 3000)) for s in speeds]

        if isinstance(acceleration, int):
            acceleration_list = [max(0, min(acceleration, 255))] * 6
        else:
            if len(acceleration) != 6:
                raise ValueError("acceleration must have length 6")
            acceleration_list = [max(0, min(a, 255)) for a in acceleration]

        logger.info(f"▶️ Starting program execution: '{self.filename}'")
        for idx, action in enumerate(self.program):
            action_type = action.get("type")
            logger.debug(f"🔹 Executing Action {idx + 1}/{len(self.program)}: Type={action_type}, Details={action}")

            try:
                if action_type == "POSE":
                    q_target = np.asarray(action["joints"])
                    if len(q_target) < robot.model.nq:
                        missing = robot.model.nq - len(q_target)
                        q_target = np.concatenate((q_target, np.zeros(missing)))

                    if not robot.check_joint_limits(q_target):
                        logger.warning(f"Action {idx + 1} (POSE) violates joint limits – skipped.")
                        continue

                    robot.set_joint_angles_animated(q_target, duration=1.0, steps=15)
                    
                    angles_rad_for_hw = q_target.tolist()[:6] 
                    arctos.move_to_angles(angles_rad_for_hw, speeds=speed_list, acceleration=acceleration_list)
                    arctos.wait_for_motors_to_stop()

                elif action_type == "WAIT":
                    duration_ms = action.get("duration_ms", 0)
                    duration_s = duration_ms / 1000.0
                    if duration_s > 0:
                        logger.info(f"⏳ Waiting for {duration_s:.2f} seconds...")
                        time.sleep(duration_s)
                    else:
                        logger.warning(f"⚠️ Invalid wait duration for action {idx + 1}: {duration_ms} ms")
                
                elif action_type == "GRIPPER":
                    command = action.get("command")
                    if command == "OPEN":
                        logger.info("🤖 Opening gripper...")
                        arctos.open_gripper()
                        time.sleep(0.5) 
                    elif command == "CLOSE":
                        logger.info("🤖 Closing gripper...")
                        arctos.close_gripper()
                        time.sleep(0.5) 
                    else:
                        logger.warning(f"⚠️ Unknown gripper command '{command}' for action {idx + 1}.")
                
                else:
                    logger.warning(f"⚠️ Unknown action type '{action_type}' for action {idx + 1} – skipped.")

            except Exception as e:
                logger.error(f"❌ Error executing action {idx + 1} ({action_type}): {e}")

        logger.info(f"✅ Program '{self.filename}' execution completed.")

    def visualize_program_actions(self, robot) -> None: 
        """
        Visualizes the 'POSE' actions from the current program in the RoboMeshCat scene.
        Non-POSE actions do not have a direct 3D visualization but are part of the program sequence.

        Args:
            robot: An instance of the ArctosPinocchioRobot class.
        """
        for obj_idx in list(self.visualized_objects.keys()): 
            try:
                robot.scene.remove_object(self.visualized_objects[obj_idx])
                del self.visualized_objects[obj_idx]
            except Exception as e:
                logger.debug(f"Error removing old visual object for index {obj_idx}: {e}")
        self.visualized_objects.clear()

        pose_actions_with_indices = [
            (original_idx, action) 
            for original_idx, action in enumerate(self.program) 
            if action.get("type") == "POSE"
        ]
        num_pose_actions = len(pose_actions_with_indices)

        for visual_order_idx, (original_program_idx, action) in enumerate(pose_actions_with_indices):
            try:
                cartesian = np.array(action["cartesian"])
                rounded = np.round(cartesian, 3)

                t = visual_order_idx / max(1, num_pose_actions - 1) if num_pose_actions > 1 else 0
                color = [round(1.0 * t, 2), round(1.0 - t, 2), 0.0]  

                name = f"PoseAction {original_program_idx+1} (Display {visual_order_idx+1}) | x={rounded[0]} y={rounded[1]} z={rounded[2]}"

                sphere = Object.create_sphere(
                    radius=0.02,
                    name=name,
                    color=color,
                    opacity=0.8
                )
                robot.scene.add_object(sphere)
                sphere.pos = cartesian
                self.visualized_objects[original_program_idx] = sphere 

            except Exception as e:
                logger.warning(f"⚠️ Error visualizing POSE action at original_program_idx {original_program_idx}: {e}")
