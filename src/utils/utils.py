"""
This module provides a collection of utility functions that are used throughout the Arctos Robot GUI application.
These functions handle tasks such as saving, loading, and executing robot poses and programs, 
controlling the robot's gripper, and updating the UI elements.
"""
import time
import numpy as np
from nicegui import ui
import logging
from threading import Thread

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------------------
# PATH PLANNING FUNCTIONS - START
# -------------------------------


def save_pose(planner, robot) -> None:
    """Saves the current robot pose.

    This function saves the current pose of the robot by capturing its current
    joint states and Cartesian coordinates. The pose is then stored using the
    provided planner instance.

    Args:
        planner: The path planner instance responsible for managing and storing
                 robot poses.
        robot: The robot instance, which provides methods to retrieve current
               joint states and Cartesian coordinates.

    Returns:
        None
    """
    time.sleep(0.5)
    planner.capture_pose(robot)
    ui.notify("✅ Pose saved successfully!")

def save_program(planner, program_name=None) -> None:
    """
    Saves the entire sequence of poses stored in the planner with an optional name.
    
    This function allows for saving the sequence of robot poses that have been
    stored in the planner. If a program name is not provided, a dialog is
    displayed to prompt the user to input a name. The program is then saved
    with the given name.

    Args:
        planner: The path planner instance containing the sequence of stored poses.
        program_name (str, optional): An optional name for the program file.
            If not provided, a dialog will be displayed to request the name. Defaults to None.

    Returns:
        None
    """
    if program_name is None:
        # Create a dialog to get the program name
        with ui.dialog() as dialog, ui.card():
            ui.label("Save Program").classes('text-xl font-bold')
            program_name_input = ui.input(label="Program Name", placeholder="Enter program name").classes('w-full')

            with ui.row().classes('w-full justify-end'):
                ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')
                ui.button("Save", on_click=lambda: save_with_name(program_name_input.value)).classes('bg-blue-700 text-white px-4 py-2 rounded-lg')

            def save_with_name(name):
                if name:
                    success, message = planner.save_program(name)
                    ui.notify(message, color='green' if success else 'red')
                else:
                    ui.notify("⚠️ Please enter a program name", color='orange')
                dialog.close()

        dialog.open()
    else:
        success, message = planner.save_program(program_name)
        ui.notify(message, color='green' if success else 'red')


def load_program(planner, pose_container=None, robot=None) -> None:
    """Load a saved program of robot poses.

    This function presents a dialog to the user, allowing them to select and
    load a previously saved program of robot poses. Upon successful loading,
    an optional UI container can be updated to display the newly loaded poses,
    and the robot's pose visualization can be updated as well.

    Args:
        planner: The path planner instance managing the pose sequence and loading.
        pose_container (ui.element, optional): An optional UI container that
            can be updated to display the loaded poses. Defaults to None.
        robot: An optional robot instance used for updating the robot's pose
            visualization. Defaults to None.

    Returns:
        None
    """
    # Get available programs
    available_programs = planner.get_available_programs()

    # Create a dialog to select the program
    with ui.dialog() as dialog, ui.card():
        ui.label("Load Program").classes('text-xl font-bold')

        if not available_programs:
            ui.label("No saved programs found").classes('text-gray-600')
        else:
            program_select = ui.select(
                options=available_programs,
                label="Select Program",
                value=available_programs[0] if available_programs else None
            ).classes('w-full')

        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')

            if available_programs:
                ui.button("Load", on_click=lambda: load_selected_program(program_select.value)).classes('bg-green-700 text-white px-4 py-2 rounded-lg')

        def load_selected_program(program_name):
            if program_name:
                success, message = planner.load_program(program_name, robot)
                ui.notify(message, color='green' if success else 'red')

                # Update pose table if container and robot are provided
                if success and pose_container is not None and robot is not None:
                    update_pose_table(planner, robot, pose_container)
            else:
                ui.notify("⚠️ Please select a program", color='orange')
                
            dialog.close()

    dialog.open()

def execute_path(planner, robot, Arctos) -> None:
    """
    Executes the planned path using a separate thread to prevent UI freezing.
    
    Args:
        planner: The path planner instance that executes the movement.
        robot: The robot instance that performs the movement.
    """
    planner.execute_path(robot, Arctos)

    ui.notify("🚀 Path executed!")

def update_pose_table(planner, robot, pose_container) -> None:
    """
    Updates the UI table to display stored poses, including joint angles and Cartesian coordinates.

    :param planner: The path planner instance managing stored poses.
    :type planner: PathPlanner
    :param robot: The robot instance required for pose deletion.
    :type robot: Robot
    :param pose_container: The UI container where the pose table will be rendered.
    :type pose_container: ui.element
    """
    
    # Clear the container

    pose_container.clear()

    with pose_container:
        ui.label("Stored Poses").classes('text-xl font-bold mb-2')

        if not planner.poses:
            ui.label("⚠️ No stored poses!").classes('text-red-500')
            return

        # Create a table for stored poses (excluding buttons)
        pose_table = ui.table(columns=[
            {"name": "pose", "label": "Pose #", "field": "pose"},
            {"name": "j1", "label": "J1 (°)", "field": "j1"},
            {"name": "j2", "label": "J2 (°)", "field": "j2"},
            {"name": "j3", "label": "J3 (°)", "field": "j3"},
            {"name": "j4", "label": "J4 (°)", "field": "j4"},
            {"name": "j5", "label": "J5 (°)", "field": "j5"},
            {"name": "j6", "label": "J6 (°)", "field": "j6"},
            {"name": "x", "label": "X (m)", "field": "x"},
            {"name": "y", "label": "Y (m)", "field": "y"},
            {"name": "z", "label": "Z (m)", "field": "z"},
        ], rows=[]).classes("w-full border")

        button_container = ui.row()  # Store delete buttons separately

        for idx, pose in enumerate(planner.poses):
            try:
                joints = [f"{np.degrees(float(j)):.2f}°" for j in pose["joints"]]
                cartesian = [f"{float(c):.3f}" for c in pose["cartesian"]]

                row = {
                    "pose": idx + 1,
                    "j1": joints[0], "j2": joints[1], "j3": joints[2],
                    "j4": joints[3], "j5": joints[4], "j6": joints[5],
                    "x": cartesian[0], "y": cartesian[1], "z": cartesian[2]
                }

                pose_table.rows.append(row)

                with button_container:
                    ui.button(f"🗑️ Delete Pose {idx + 1}", on_click=lambda i=idx: delete_pose(planner, i, robot, pose_container)).classes('bg-red-500 text-white px-3 py-1 rounded-lg mt-1')

            except Exception as e:
                print(f"⚠️ Error displaying pose {idx}: {e}")

def delete_pose(planner, index, robot, pose_container) -> None:
    """
    Deletes a stored pose, updates the UI table, and removes the corresponding MeshCat visualization.

    :param planner: The path planner instance managing stored poses.
    :type planner: PathPlanner
    :param index: The index of the pose to be deleted.
    :type index: int
    :param robot: The robot instance required to remove the visualization from MeshCat.
    :type robot: Robot
    """
    planner.delete_pose(index, robot)  # Call delete function in PathPlanner
    update_pose_table(planner, robot, pose_container)

# ------------------------------
# PATH PLANNING FUNCTIONS - END
# ------------------------------



# ------------------------------
# STARTUP/SLEEP FUNCTIONS
# ------------------------------


def run_move_can(robot, arctos) -> None:
    """Run the robot movement process in a separate thread.

    This function initiates the robot's movement in a separate thread to
    prevent the main UI thread from being blocked, ensuring the GUI remains
    responsive. It retrieves the current joint angles, moves the robot to those
    angles, and waits for the motors to come to a stop.

    Args:
        robot: The robot instance providing joint angle information.
        arctos: The robot controller used to execute the movement.

    Returns:
        None
    """
    def task():
        joint_positions_rad = robot.get_current_joint_angles()
        if joint_positions_rad is None:
            ui.notify("❌ No valid joint positions received!", color='red')
            return

        arctos.move_to_angles(joint_positions_rad)
        arctos.wait_for_motors_to_stop()

    Thread(target=task, daemon=True).start()
    ui.notify("✅ Robot moved successfully!", color='green')


def set_zero_position(robot) -> None:
    """Move the robot to its zero position.

    This function moves the robot to a predefined zero position, where all
    joint angles are set to 0 radians.

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
    Sends a command to open the gripper.
    Args:
        Arctos: The robot controller interface.

    """
    Arctos.open_gripper()
    ui.notify("✅ Gripper opened.")

def close_gripper(Arctos) -> None:
    """
    Sends a command to close the gripper.
    Args:
        Arctos: The robot controller interface.

    """
    Arctos.close_gripper()
    ui.notify("✅ Gripper closed.")

# ------------------------------
# POSITION CONTROL FUNCTIONS
# ------------------------------



# Functions to update joint states

def update_joint_states(robot, joint_positions):
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions[i].set_text(f"Joint {i+1}: {np.degrees(robot.q[i]):.2f}°")  # Umrechnung in Grad

def update_joint_states_encoder(robot, joint_positions_encoder):
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions_encoder[i].set_text(f"Joint {i+1}: {np.degrees(robot.q_encoder[i]):.2f}°")  # Umrechnung in Grad

def live_update_ee_postion(robot, ee_position_labels):
    """Liest die aktuelle Endeffektor-Position aus `robot` und aktualisiert die UI in Echtzeit."""
    if robot:  # Sicherstellen, dass `robot` initialisiert ist
        ee_pos = robot.get_end_effector_position()  # Holt die Position als np.array [x, y, z]
        for i, axis in enumerate(["X", "Y", "Z"]):
            ee_position_labels[axis].set_text(f"{axis}: {ee_pos[i]:.2f} m")  # Setzt die UI-Werte

def live_update_ee_orientation(robot, ee_orientation_labels):
    """Liest die aktuelle Endeffektor-Orientierung aus `robot` und aktualisiert die UI in Echtzeit."""
    if robot:  # Sicherstellen, dass `robot` existiert
        ee_orient = np.degrees(robot.get_end_effector_orientation())  # In Grad umwandeln

        for i, axis in enumerate(["Roll", "Pitch", "Yaw"]):
            ee_orientation_labels[axis].set_text(f"{axis}: {ee_orient[i]:.2f}°")  # UI aktualisieren

def set_ee_position_from_input(robot, ee_position_inputs):
    """Reads the XYZ inputs from the UI and moves the robot to the new position using inverse kinematics."""
    try:
        x = ee_position_inputs["X"].value
        y = ee_position_inputs["Y"].value
        z = ee_position_inputs["Z"].value

        if None in [x, y, z]:  # Falls ein Feld leer ist
            ui.notify("❌ Bitte alle Werte für X, Y, Z eingeben!", color='red')
            return

        # Berechnung der neuen Gelenkwinkel mit Inverser Kinematik
        target_xyz = np.array([x, y, z])
        q_solution = robot.inverse_kinematics_pink(target_xyz)

        # Bewegung ausführen
        robot.set_joint_angles_animated(q_solution, duration=1.0, steps=50)
        ui.notify(f"✅ Moved to position: X={x}, Y={y}, Z={z}")

    except ValueError as e:
        ui.notify(f"❌ IK Fehler: {str(e)}", color='red')
    except Exception as e:
        ui.notify(f"❌ Fehler: {str(e)}", color='red')


def set_ee_orientation_from_input(robot, ee_orientation_inputs):
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
        robot.set_joint_angles_animated(q_solution, duration=1.5, steps=50)

        ui.notify("✅ End-Effector Orientation Updated!")

    except ValueError as e:
        ui.notify(f"❌ IK Fehler: {str(e)}", type="error")
    except Exception as e:
        ui.notify(f"❌ Error: {e}", type="error")


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
        robot.set_joint_angles_animated(q_solution, duration=1.5, steps=50)

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
    """Set the robot's joint angles based on input from the GUI.

    This function updates the robot's joint angles to the values specified in
    the GUI input fields. It reads the input values for the first six joints
    and updates the robot's configuration accordingly, followed by an animated movement.

    Args:
        robot: The robot instance to update.
        new_joint_inputs: A list of UI input elements representing the new joint values.
    """
    if robot:
        q_target = robot.q.copy()
        for i in range(6):
            if new_joint_inputs[i].value is not None:
                q_target[i] = np.radians(new_joint_inputs[i].value)
        ui.notify("Robot moving to joint angles...")
        robot.set_joint_angles_animated(q_target, duration=1.0, steps=50)

def reset_to_zero_position(robot):
    """Moves the robot back to its default zero position, ensuring the correct shape for q_target."""
    if robot:
        q_target = robot.q.copy()
        q_target[:6] = 0
        robot.set_joint_angles_animated(q_target, duration=0.5, steps=50)
    else:
        ui.notify("⚠️ Robot instance not found!", type="warning")



# ----------------------------------
# KEYBOARD CONTROL FUNCTIONS - START
# ----------------------------------

keyboard_control_active = False
key_states = {}
step_size_input = None


def toggle_keyboard_control():
    """Toggle keyboard control.

    Toggles keyboard control on/off and updates the UI to reflect the current state.
    """
    global keyboard_control_active 
    keyboard_control_active = not keyboard_control_active  

    if keyboard_control_active:
        ui.notify("🎮 Keyboard control activated!", color="green")
    else:
        key_states.clear()
        ui.notify("🛑 Keyboard control deactivated!", color="red")

def adjust_position(robot, Arctos):
    """Adjust robot position.

    This function incrementally adjusts the robot's end-effector position
    based on the currently pressed keys, providing a fine-grained control
    mechanism.

    Args:
        robot: The robot instance to move.
        Arctos: The robot controller interface.
    """
    if not keyboard_control_active:
        return

    current_position = robot.get_end_effector_position()
    current_orientation = robot.get_end_effector_orientation()

    step = step_size_input.value if step_size_input and step_size_input.value else 0.002

    if 'a' in key_states:
        current_position[0] -= step
    if 'd' in key_states:
        current_position[0] += step
    if 'q' in key_states:
        current_position[2] += step
    if 'e' in key_states:
        current_position[2] -= step
    if 'w' in key_states:
        current_position[1] -= step
    if 's' in key_states:
        current_position[1] += step

    try:
        q_solution = robot.inverse_kinematics_pink(current_position, current_orientation)
        robot.instant_display_state(q_solution)
    except ValueError as e:
        logger.warning(f"⚠️ IK Fehler bei Tastatureingabe: {e}")
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler bei adjust_position: {e}")


def on_key(event, robot, Arctos):
    """Handles keyboard events using NiceGUI."""
    global key_states

    if not keyboard_control_active:
        return

    if event.action.keydown:
        key_states[event.key.name] = True
    elif event.action.keyup:
        key_states.pop(event.key.name, None)

    adjust_position(robot, Arctos)

def initialize_keyboard_listeners(robot, Arctos):
    """Initialize keyboard listeners.

    Initializes the keyboard listeners within the NiceGUI framework to capture
    keyboard events for robot control.

    Args:
        robot: The robot instance to be controlled.
        Arctos: The robot controller interface.
    """
    ui.keyboard(lambda event: on_key(event, robot, Arctos), ignore=[])
    logger.info("🎮 Keyboard control initialized via `ui.keyboard()`")

# ----------------------------------
# KEYBOARD CONTROL FUNCTIONS - END
# ----------------------------------

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

    This function starts a separate thread to update the robot's joint states,
    preventing the UI from freezing during this potentially time-consuming operation.

    Args:
        robot: The robot instance to be controlled.
        Arctos: The robot controller interface.
    """
    def task():
        try:
            initialize_current_joint_states(robot, Arctos)
        except Exception as e:
            print(f"❌ Error updating joint states: {e}")
    Thread(target=task, daemon=True).start()
