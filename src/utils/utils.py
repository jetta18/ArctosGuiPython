"""
This module provides a collection of utility functions used throughout the Arctos Robot GUI application.
These functions handle tasks such as saving, loading, and executing robot poses and programs, 
controlling the robot's gripper, and updating UI elements.
"""
import time
import numpy as np
from nicegui import ui
import threading
import time
import logging
from threading import Thread

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ------------------------------
# STARTUP/SLEEP FUNCTIONS
# ------------------------------


def run_move_can(robot, arctos, settings_manager) -> None:
    """
    Move the physical robot to the current joint positions using per-joint speeds.

    Uses the speeds defined in settings ('joint_speeds'). Defaults to 500 RPM if not specified.

    Args:
        robot: The robot instance to move.
        arctos: The robot controller interface.
        settings_manager: The settings manager instance providing speed settings.

    Returns:
        None

    Raises:
        Exception: For any errors during robot movement or communication.
    """
    def task():
        q_rad = robot.get_current_joint_angles()
        if q_rad is None:
            ui.notify("No valid joint positions!", color="red")
            return

        # Build the 6-element speed list, clamped to 0-3000
        joint_speeds = settings_manager.get("joint_speeds", {})
        speeds = [max(0, min(joint_speeds.get(i, 500), 3000)) for i in range(6)]
        
        # --- Acceleration: per joint, clamped ---
        joint_accelerations = settings_manager.get("joint_accelerations", {})
        accelerations = [max(0, min(joint_accelerations.get(i, 150), 255)) for i in range(6)]

        # --- Move the robot ---
        arctos.move_to_angles(q_rad, speeds=speeds, acceleration=accelerations)
        
    Thread(target=task, daemon=True).start()
    ui.notify("Robot moving...", color="green")


def set_zero_position(robot) -> None:
    """
    Move the robot to its zero position.

    Moves the robot to a predefined zero position, where all joint angles are set to 0 radians.

    Args:
        robot: The robot instance to move.
    """
    robot.q = np.zeros(robot.model.nq)
    robot.display()
    ui.notify("✅ Robot moved to zero position.")



# ------------------------------
# GRIPPER CONTROL FUNCTIONS
# ------------------------------


def open_gripper(Arctos) -> None:
    """
    Sends a command to open the robot's gripper.

    Args:
        Arctos: The robot controller interface that manages hardware commands.

    Returns:
        None

    Raises:
        Exception: If the gripper command fails, an exception may be raised by the controller.
    """
    Arctos.open_gripper()
    ui.notify("✅ Gripper opened.")

def close_gripper(Arctos) -> None:
    """
    Sends a command to close the robot's gripper.

    Args:
        Arctos: The robot controller interface that manages hardware commands.

    Returns:
        None

    Raises:
        Exception: If the gripper command fails, an exception may be raised by the controller.
    """
    Arctos.close_gripper()
    ui.notify("✅ Gripper closed.")

# ------------------------------
# POSITION CONTROL FUNCTIONS
# ------------------------------



# Functions to update joint states

def update_joint_states(robot, joint_positions):
    """
    Updates the UI labels with the robot's current joint positions (in degrees).

    Args:
        robot: The robot instance containing the current joint state (robot.q).
        joint_positions (list): List of UI label elements to update with joint values.

    Returns:
        None

    Raises:
        AttributeError: If robot.q is not available or not iterable.
        Exception: For any unexpected UI or robot errors.
    """
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions[i].set_text(f"Joint {i+1}: {np.degrees(robot.q[i]):.2f}°")  # Umrechnung in Grad

def update_joint_states_encoder(robot, joint_positions_encoder):
    """
    Updates the UI labels with the robot's encoder joint positions (in degrees).

    Args:
        robot: The robot instance containing the encoder joint state (robot.q_encoder).
        joint_positions_encoder (list): List of UI label elements to update with encoder joint values.

    Returns:
        None

    Raises:
        AttributeError: If robot.q_encoder is not available or not iterable.
        Exception: For any unexpected UI or robot errors.
    """
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions_encoder[i].set_text(f"Joint {i+1}: {np.degrees(robot.q_encoder[i]):.2f}°")  # Umrechnung in Grad

def live_update_ee_postion(robot, ee_position_labels):
    """
    Reads the current end-effector position from the robot and updates the UI labels in real time.

    Args:
        robot: The robot instance providing the end-effector position (robot.get_end_effector_position()).
        ee_position_labels (dict): Dictionary of UI label elements keyed by axis ("X", "Y", "Z").

    Returns:
        None

    Raises:
        AttributeError: If the robot does not provide position data or UI labels are missing.
        Exception: For any unexpected UI or robot errors.
    """
    if robot:  # Sicherstellen, dass `robot` initialisiert ist
        ee_pos = robot.get_end_effector_position()  # Holt die Position als np.array [x, y, z]
        for i, axis in enumerate(["X", "Y", "Z"]):
            ee_position_labels[axis].set_text(f"{axis}: {ee_pos[i]:.2f} m")  # Setzt die UI-Werte

def live_update_ee_orientation(robot, ee_orientation_labels):
    """
    Reads the current end-effector orientation from the robot and updates the UI labels in real time.

    Args:
        robot: The robot instance providing the end-effector orientation (robot.get_end_effector_orientation()).
        ee_orientation_labels (dict): Dictionary of UI label elements keyed by axis ("Roll", "Pitch", "Yaw").

    Returns:
        None

    Raises:
        AttributeError: If the robot does not provide orientation data or UI labels are missing.
        Exception: For any unexpected UI or robot errors.
    """
    if robot:  # Sicherstellen, dass `robot` existiert
        ee_orient = np.degrees(robot.get_end_effector_orientation())  # In Grad umwandeln

        for i, axis in enumerate(["Roll", "Pitch", "Yaw"]):
            ee_orientation_labels[axis].set_text(f"{axis}: {ee_orient[i]:.2f}°")  # UI aktualisieren

def set_ee_position_from_input(robot, ee_position_inputs):
    """
    Reads the XYZ position inputs from the UI and moves the robot to the new position using inverse kinematics.

    Args:
        robot: The robot instance to be moved.
        ee_position_inputs (dict): Dictionary of UI input elements for "X", "Y", and "Z" axes.

    Returns:
        None

    Raises:
        ValueError: If inverse kinematics fails to find a solution for the target position.
        Exception: For any unexpected UI or robot errors.
    """
    try:
        x = ee_position_inputs["X"].value
        y = ee_position_inputs["Y"].value
        z = ee_position_inputs["Z"].value

        if None in [x, y, z]:  # Falls ein Feld leer ist
            ui.notify("❌ Please enter values for X, Y, and Z!", color='red')
            return

        # Berechnung der neuen Gelenkwinkel mit Inverser Kinematik
        target_xyz = np.array([x, y, z])
        q_solution = robot.inverse_kinematics_pink(target_xyz)

        # Bewegung ausführen
        robot.set_joint_angles_animated(q_solution, duration=1.0, steps=15)
        ui.notify(f"✅ Moved to position: X={x}, Y={y}, Z={z}")

    except ValueError as e:
        ui.notify(f"❌ IK error: {str(e)}", color='red')
    except Exception as e:
        ui.notify(f"❌ Error: {str(e)}", color='red')


def set_ee_orientation_from_input(robot, ee_orientation_inputs):
    """
    Reads the RPY (Roll, Pitch, Yaw) orientation inputs from the UI and moves the robot to the new orientation using inverse kinematics.

    Args:
        robot: The robot instance to be moved.
        ee_orientation_inputs (dict): Dictionary of UI input elements for "Roll", "Pitch", and "Yaw" axes.

    Returns:
        None

    Raises:
        ValueError: If inverse kinematics fails to find a solution for the target orientation.
        Exception: For any unexpected UI or robot errors.
    """
    """Reads the RPY inputs from the UI and moves the robot to the new orientation using inverse kinematics."""
    try:
        # Eingaben aus der UI auslesen und von Grad in Radians umwandeln
        roll = np.radians(ee_orientation_inputs["Roll"].value or 0.0)
        pitch = np.radians(ee_orientation_inputs["Pitch"].value or 0.0)
        yaw = np.radians(ee_orientation_inputs["Yaw"].value or 0.0)

        target_rpy = np.array([roll, pitch, yaw])

        # Aktuelle XYZ-Position beibehalten
        current_xyz = robot.get_end_effector_position()

        # Berechnung der neuen Gelenkwinkel mit Inverser Kinematik
        q_solution = robot.inverse_kinematics_pink(current_xyz, target_rpy)

        # Bewegung ausführen
        robot.set_joint_angles_animated(q_solution, duration=1.5, steps=15)

        ui.notify("✅ End-Effector Orientation Updated!")

    except ValueError as e:
        ui.notify(f"❌ IK error: {str(e)}", color='red')
    except Exception as e:
        ui.notify(f"❌ Error: {e}", color='red')


def set_ee_pose_from_input(robot, ee_position_inputs, ee_orientation_inputs, use_orientation: bool):
    """
    Sets the end-effector pose based on user input from the UI.

    This function reads the XYZ position and, optionally, the RPY (roll, pitch, yaw) orientation 
    from UI input fields. It then performs inverse kinematics to calculate the required joint angles 
    and moves the robot to the desired pose.

    Args:
        robot: The robot instance providing kinematics and motion methods.
        ee_position_inputs (dict): A dictionary with UI number fields for X, Y, and Z.
        ee_orientation_inputs (dict): A dictionary with UI number fields for Roll, Pitch, and Yaw.
        use_orientation (bool): If True, RPY orientation will be used; otherwise, only position is considered.
    """
    try:
        # Read position inputs
        x = ee_position_inputs["X"].value
        y = ee_position_inputs["Y"].value
        z = ee_position_inputs["Z"].value

        # Validate inputs
        if None in [x, y, z]:
            ui.notify("❌ Please enter values for X, Y, and Z!", color='red')
            return

        target_xyz = np.array([x, y, z])

        # Read and convert orientation inputs if enabled
        if use_orientation:
            roll = np.radians(ee_orientation_inputs["Roll"].value or 0.0)
            pitch = np.radians(ee_orientation_inputs["Pitch"].value or 0.0)
            yaw = np.radians(ee_orientation_inputs["Yaw"].value or 0.0)
            target_rpy = np.array([roll, pitch, yaw])
        else:
            target_rpy = None

        # Compute joint angles via inverse kinematics
        q_solution = robot.inverse_kinematics_pink(target_xyz, target_rpy)

        # Animate motion to the new pose
        robot.set_joint_angles_animated(q_solution, duration=1.5, steps=15)

        # Notify user
        msg = f"✅ Moved to position: X={x:.3f}, Y={y:.3f}, Z={z:.3f}"
        if use_orientation:
            rpy_deg = np.degrees(target_rpy)
            msg += f", Roll={rpy_deg[0]:.1f}°, Pitch={rpy_deg[1]:.1f}°, Yaw={rpy_deg[2]:.1f}°"
        ui.notify(msg)

    except ValueError as e:
        ui.notify(f"❌ IK error: {str(e)}", color='red')
    except Exception as e:
        ui.notify(f"❌ Unexpected error: {str(e)}", color='red')


def set_joint_angles_from_gui(robot, new_joint_inputs):
    """
    Set the robot's joint angles based on input from the GUI.

    Reads input values for the first six joints from the GUI and updates the robot's configuration. Executes an animated movement to the new joint angles.

    Args:
        robot: The robot instance to update.
        new_joint_inputs (list): List of UI input elements representing the new joint values.

    Returns:
        None
    """
    if robot:
        q_target = robot.q.copy()
        for i in range(6):
            if new_joint_inputs[i].value is not None:
                q_target[i] = np.radians(new_joint_inputs[i].value)
        ui.notify("Robot moving to joint angles...")
        robot.set_joint_angles_animated(q_target, duration=1.5, steps=15)

def reset_to_zero_position(robot):
    """Moves the robot back to its default zero position, ensuring the correct shape for q_target."""
    if robot:
        q_target = robot.q.copy()
        q_target[:6] = 0
        robot.set_joint_angles_animated(q_target, duration=1.5, steps=15)
    else:
        ui.notify("⚠️ Robot instance not found!", type="warning")


def initialize_current_joint_states(robot, Arctos):
    """
    Read and initialize the robot's current joint states.
    This function reads the current joint angles from the robot's encoders and updates the 3D model correctly.
    """
    current_joint_states = Arctos.get_joint_angles()

    # Extract joint angles for calculation
    a4 = (current_joint_states[4] + current_joint_states[5]) / 2  # Reverse B-axis formula
    a5 = (current_joint_states[4] - current_joint_states[5]) / 2  # Reverse C-axis formula

    # Assign the corrected values to the robot state
    robot.q_encoder[:6] = [
        current_joint_states[0],  # A0
        current_joint_states[1],  # A1
        current_joint_states[2],  # A2
        current_joint_states[3],  # A3 remains unchanged
        a4,  # Corrected A4 based on B-axis calculations
        a5   # Corrected A5 based on C-axis calculations
    ]

def threaded_initialize_current_joint_states(robot, Arctos):
    """
    Update the robot's joint states in a separate thread.

    Starts a daemon thread to update the robot's joint states using the provided
    robot and controller interface. This prevents the UI from freezing during
    potentially time-consuming operations.

    Args:
        robot: The robot instance to be updated.
        Arctos: The robot controller interface.

    Returns:
        None

    Raises:
        Exception: If updating the joint states fails, prints the error message.
    """
    def task():
        try:
            initialize_current_joint_states(robot, Arctos)
        except Exception as e:
            print(f"Error updating joint states: {e}")
    Thread(target=task, daemon=True).start()

# Global scaling variable for speed
speed_scale = 1.0

def set_speed_scale(val: float) -> None:
    """
    Update the global speed scaling factor.

    Sets the global speed_scale variable to the provided value, which should be in the range 0.1 to 2.0. This scaling factor is used to adjust robot movement speeds globally.

    Args:
        val (float): The new speed scaling factor (recommended range: 0.1 to 2.0).

    Returns:
        None
    """
    global speed_scale
    speed_scale = val
