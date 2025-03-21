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
    """
    Runs the movement process in a separate thread to avoid blocking the UI.
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

def open_gripper(Arctos) -> None:
    """
    Sends a command to open the gripper.
    
    Args:
        arctos: The robot controller interface.
    """
    Arctos.open_gripper()
    ui.notify("✅ Gripper opened.")

def close_gripper(Arctos) -> None:
    """
    Sends a command to close the gripper.
    
    Args:
        arctos: The robot controller interface.
    """
    Arctos.close_gripper()
    ui.notify("✅ Gripper closed.")



# ------------------------------
# POSITION CONTROL FUNCTIONS
# ------------------------------
def update_joint_states(robot, joint_positions):
    if robot:  # Stelle sicher, dass `robot` initialisiert ist
        for i in range(6):
            joint_positions[i].set_text(f"Joint {i+1}: {np.degrees(robot.q_encoder[i]):.2f}°")  # Umrechnung in Grad


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

        # Aktuelle RPY-Werte beibehalten
        current_rpy = robot.get_end_effector_orientation()

        # Berechnung der neuen Gelenkwinkel mit Inverser Kinematik
        target_xyz = np.array([x, y, z])
        q_solution = robot.inverse_kinematics(target_xyz, current_rpy)

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
        q_solution = robot.inverse_kinematics(current_xyz, target_rpy)

        # Bewegung ausführen
        robot.set_joint_angles_animated(q_solution, duration=1.5, steps=50)
        ui.notify("✅ End-Effector Orientation Updated!")

    except ValueError as e:
        ui.notify(f"❌ IK Fehler: {str(e)}", type="error")
    except Exception as e:
        ui.notify(f"❌ Error: {e}", type="error")



def set_joint_angles_from_gui(robot, new_joint_inputs):
    if robot:
        q_target = robot.q.copy()
        for i in range(6):  # Nur die ersten 6 Gelenke setzen
            if new_joint_inputs[i].value is not None:
                q_target[i] = np.radians(new_joint_inputs[i].value)
        ui.notify("Robot moving to joint angles...")
        robot.set_joint_angles_animated(q_target, duration=1.0, steps=50)  # Animation über 1.5 Sekunden

def reset_to_zero_position(robot):
    """Moves the robot back to its default zero position, ensuring the correct shape for q_target."""
    if robot:
        q_target = robot.q.copy()  # Kopiere die aktuelle Gelenkkonfiguration
        q_target[:6] = 0  # Setze nur die ersten 6 Gelenke auf 0
        
        #ui.notify("🔄 Moving robot to to zero position...")
        robot.set_joint_angles_animated(q_target, duration=0.5, steps=50)  # Animierte Bewegung
    else:
        ui.notify("⚠️ Robot instance not found!", type="warning")



# ----------------------------------
# KEYBOARD CONTROL FUNCTIONS - START
# ----------------------------------
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
# ----------------------------------
# KEYBOARD CONTROL FUNCTIONS - END
# ----------------------------------




def initialize_current_joint_states(robot, Arctos):
    """
    Reads the current joint angles from the robot's encoders and updates the 3D model correctly.

    This function ensures that the inverse kinematics of the B and C axes are correctly reversed,
    so the 3D model matches the real robot's state.

    :param robot: The Pinocchio-based robot model.
    :param Arctos: The real robot controller that provides encoder values.
    """
    current_joint_states = Arctos.get_joint_angles()  # Get raw joint angles from encoders

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

    # Update the visualization with the new joint angles
    #robot.instant_display_state()
    
def threaded_initialize_current_joint_states(robot, Arctos):
    def task():
        try:
            initialize_current_joint_states(robot, Arctos)
        except Exception as e:
            print(f"❌ Error updating joint states: {e}")
    Thread(target=task, daemon=True).start()


