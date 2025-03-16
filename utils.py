import time
import numpy as np
import os
import threading
from nicegui import ui
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  

# ------------------------------
# PATH PLANNING FUNCTIONS
# ------------------------------

def save_pose(planner, robot) -> None:
    """
    Saves the current robot pose by retrieving joint states from MoveIt!
    and storing them using the planner.
    
    Args:
        planner: The path planner instance used to manage stored poses.
        robot: The robot instance from which the joint states are retrieved.
    """
    time.sleep(0.5)  
    planner.capture_pose(robot)
    ui.notify("✅ Pose saved successfully!")

def save_program(planner) -> None:
    """
    Saves the entire sequence of poses stored in the planner.
    
    Args:
        planner: The path planner instance that manages the pose sequence.
    """
    planner.save_program()
    ui.notify("✅ Program saved!")

def load_program(planner) -> None:
    """
    Loads a previously saved sequence of poses into the planner.
    
    Args:
        planner: The path planner instance that manages the pose sequence.
    """
    planner.load_program()
    ui.notify("✅ Program loaded!")

def execute_path(planner, robot) -> None:
    """
    Executes the planned path using a separate thread to prevent UI freezing.
    
    Args:
        planner: The path planner instance that executes the movement.
        robot: The robot instance that performs the movement.
    """
    planner.execute_path(robot)
    ui.notify("🚀 Executing path...")



# ------------------------------
# STARTUP/SLEEP FUNCTIONS
# ------------------------------

def run_move_can(robot, arctos) -> None:
    """
    Retrieves joint states and moves the robot accordingly.
    
    Args:
        robot: The robot instance.
        arctos: The control interface for the robot.
    """
    joint_positions_rad = robot.get_current_joint_angles()
    if joint_positions_rad is None:
        ui.notify("❌ No valid joint positions received!", color='red')
        return
    #arctos.wait_for_motors_to_stop()
    arctos.move_to_angles(joint_positions_rad)
    ui.notify("✅ Robot moved successfully!")

def set_zero_position(robot) -> None:
    """
    Moves the robot to a zero position where all joints are set to 0 radians.
    
    Args:
        robot: The robot instance.
    """
    robot.q = np.zeros(robot.model.nq)
    robot.display()
    ui.notify("✅ Robot moved to zero position.")



# ------------------------------
# GRIPPER CONTROL FUNCTIONS
# ------------------------------

def open_gripper(arctos) -> None:
    """
    Sends a command to open the gripper.
    
    Args:
        arctos: The robot controller interface.
    """
    arctos.open_gripper()
    ui.notify("✅ Gripper opened.")

def close_gripper(arctos) -> None:
    """
    Sends a command to close the gripper.
    
    Args:
        arctos: The robot controller interface.
    """
    arctos.close_gripper()
    ui.notify("✅ Gripper closed.")




# ------------------------------
# POSITION CONTROL FUNCTIONS
# ------------------------------
def move_robot_to_xyz(robot, x, y, z) -> None:
    """
    Moves the robot to a specified XYZ position using inverse kinematics.
    
    Args:
        robot: The robot instance.
        x (float): X-coordinate in meters.
        y (float): Y-coordinate in meters.
        z (float): Z-coordinate in meters.
    """
    try:
        target_position = np.array([x, y, z])
        target_rpy = np.array([np.pi/4, 0, 0])
        q_solution = robot.inverse_kinematics(target_position, target_rpy)
        robot.set_joint_angles_animated(q_solution, duration=1.0, steps=50)
        ui.notify(f"✅ Moved to position: X={x}, Y={y}, Z={z}")
    except ValueError:
        ui.notify("❌ Invalid input! Please enter numerical values for X, Y, and Z.", color='red')



def update_joint_states(robot, joint_positions):
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions[i].set_text(f"Gelenk {i+1}: {np.degrees(robot.q[i]):.2f}°")  # Umrechnung in Grad


def update_ee_postion(robot, ee_position_labels):
    """Liest die aktuelle Endeffektor-Position aus `robot` und aktualisiert die UI in Echtzeit."""
    if robot:  # Sicherstellen, dass `robot` initialisiert ist
        ee_pos = robot.get_end_effector_position()  # Holt die Position als np.array [x, y, z]
        for i, axis in enumerate(["X", "Y", "Z"]):
            ee_position_labels[axis].set_text(f"{axis}: {ee_pos[i]:.2f} mm")  # Setzt die UI-Werte

def set_cartesian_values_from_gui(robot, ee_position_inputs):
    if robot:  # Sicherstellen, dass `robot` existiert
        try:
            x = ee_position_inputs["X"].value
            y = ee_position_inputs["Y"].value
            z = ee_position_inputs["Z"].value

            if None in [x, y, z]:  # Falls ein Feld leer ist
                ui.notify("❌ Bitte alle Werte für X, Y, Z eingeben!", color='red')
                return
    
            move_robot_to_xyz(robot, x, y, z)  # Bewegung ausführen

        except Exception as e:
            ui.notify(f"❌ Fehler: {str(e)}", color='red')

def set_joint_angles_from_gui(robot, new_joint_inputs):
    if robot:
        q_target = robot.q.copy()
        for i in range(6):  # Nur die ersten 6 Gelenke setzen
            if new_joint_inputs[i].value is not None:
                q_target[i] = np.radians(new_joint_inputs[i].value)
        robot.set_joint_angles_animated(q_target, duration=1.0, steps=50)  # Animation über 1.5 Sekunden
    ui.notify("Gelenkwinkel animiert gesetzt!")


keyboard_control_active = False  # Toggle state
key_states = {}  # Tracks pressed keys
STEP_SIZE = 0.002  # Movement step size

def toggle_keyboard_control():
    """Toggles keyboard control on/off and updates UI."""
    global keyboard_control_active  
    keyboard_control_active = not keyboard_control_active  

    if keyboard_control_active:
        ui.notify("🎮 Keyboard control activated!", color="green")
    else:
        key_states.clear()
        ui.notify("🛑 Keyboard control deactivated!", color="red")

def adjust_position(robot, Arctos):
    """Moves the robot incrementally based on pressed keys."""
    if not keyboard_control_active:
        return

    current_position = robot.get_end_effector_position()

    if 'a' in key_states: current_position[0] -= STEP_SIZE
    if 'd' in key_states: current_position[0] += STEP_SIZE
    if 'q' in key_states: current_position[2] += STEP_SIZE
    if 'e' in key_states: current_position[2] -= STEP_SIZE
    if 'w' in key_states: current_position[1] -= STEP_SIZE
    if 's' in key_states: current_position[1] += STEP_SIZE

    logger.debug(f"📍 Moving to: {current_position}")  # Debugging
    robot.instant_display_state(robot.inverse_kinematics(current_position))
    #run_move_can(robot, Arctos)

def on_key(event, robot, Arctos):
    """Handles keyboard events using NiceGUI."""
    global key_states

    if not keyboard_control_active:
        return

    if event.action.keydown:
        key_states[event.key.name] = True
    elif event.action.keyup:
        key_states.pop(event.key.name, None)

    adjust_position(robot, Arctos)  # Move immediately on key press

def initialize_keyboard_listeners(robot, Arctos):
    """Initializes the keyboard listener in NiceGUI."""
    ui.keyboard(lambda event: on_key(event, robot, Arctos), ignore=[])
    logger.info("🎮 Keyboard control initialized via `ui.keyboard()`")


def initilize_current_joint_states(robot, Arctos):
    current_joint_states = Arctos.get_joint_angles()
    # Update only the first 6 elements of robot.q
    robot.q[:6] = current_joint_states
    robot.instant_display_state()