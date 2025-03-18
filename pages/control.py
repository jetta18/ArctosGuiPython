from nicegui import ui
import datetime
import numpy as np
import asyncio

# Import local modules
from arctos_controller import ArctosController
from path_planning import PathPlanner
import homing
import utils
from ArctosPinocchio import ArctosPinocchioRobot

MESH_CAT_URL = "http://127.0.0.1:7000/static/"

Arctos = None
robot = None
planner = None

async def initialize_robot():
    """
    Initializes the robot with a loading animation and success notification.
    """
    global Arctos, robot, planner

    ui.notify("⏳ Initializing robot...", color="blue")

    # 🛠 Execute blocking initialization in a separate thread
    await asyncio.to_thread(_initialize_robot_blocking)

    ui.notify("✅ Robot successfully initialized! Reloading page...", color="green")

    # 🔄 Reload page after initialization
    await asyncio.sleep(1.5)  # Short delay for user visibility
    ui.navigate.to('/control')

def _initialize_robot_blocking():
    """Blocking initialization of the robot."""
    global Arctos, robot, planner
    Arctos = ArctosController()
    robot = ArctosPinocchioRobot()
    planner = PathPlanner()

def live_update_ee_orientation():
    """Reads the current end-effector orientation from `robot` and updates the UI in real-time."""
    #utils.update_ee_orientation(robot, ee_orientation_labels)

def set_ee_orientation_from_input():
    """Reads the inputs for Roll, Pitch, and Yaw from the UI and moves the robot to the new orientation."""
    #utils.set_orientation_values_from_gui(robot, ee_orientation_inputs)



def create():
    """
    Creates the control page for robot operation.
    """
    ui.label("Control").classes('text-3xl font-bold text-center mb-4')
    # 🎮 Add keyboard listener directly in `create()`
    ui.keyboard(lambda event: utils.on_key(event, robot, Arctos))
    # Layout with two columns: Control on the left | Visualization & Console on the right
    with ui.grid(columns=2).classes('gap-4'):

        # --- LEFT SECTION: Control ---
        with ui.column():
            # 🌟 Button to initialize the robot 
            ui.button("🔄 Initialize Robot", on_click=initialize_robot).classes('bg-blue-500 text-white w-full mt-2 py-2 rounded-lg')            
            # Home and Sleep Pose buttons
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("🏠 Move to Home Pose", on_click=lambda: homing.move_to_zero_pose(Arctos)).classes('bg-purple-500 text-white px-4 py-2 rounded-lg')
                ui.button("💤 Move to Sleep Pose", on_click=lambda: homing.move_to_sleep_pose(Arctos)).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')
                # --- New button to start movement ---
                ui.button("▶️ Start Movement", on_click=lambda: utils.run_move_can(robot, Arctos)).classes('bg-red-500 text-white w-full mt-2 py-2 rounded-lg')
                
            # --- Joint Control in the UI ---
            with ui.card().classes('w-full p-4'):
                ui.label("🦾 Joint Control").classes('text-xl font-bold mb-2')
                
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    joint_positions = [ui.label(f"Joint {i+1}: 0.0°").classes('text-lg w-full text-center') for i in range(6)]
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    new_joint_inputs = [ui.number(label=f"Joint {i+1} (°)").classes('w-full') for i in range(6)]  # Input fields
                
                # button to set joint angles
                ui.button("✅ Set Joint Angles", on_click=lambda: utils.set_joint_angles_from_gui(robot, new_joint_inputs)).classes(
                    'bg-green-500 text-white w-full mt-2 py-2 rounded-lg')
                
            # --- Cartesian Position of the End-Effector ---
            with ui.card().classes('w-full p-4 mt-2'):
                ui.label("📍 End-Effector Position").classes('text-xl font-bold mb-2')
                
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    ee_position_labels = {axis: ui.label(f"{axis}: 0.00 mm").classes('text-lg w-full text-center') for axis in ["X", "Y", "Z"]}
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    ee_position_inputs = {axis: ui.number(label=f"{axis} (mm)").classes('w-full') for axis in ["X", "Y", "Z"]}
                
                # Button to set end-effector position
                ui.button("✅ Set End-Effector Position", on_click=lambda: utils.set_cartesian_values_from_gui(robot, ee_position_inputs)).classes(
                    'bg-green-500 text-white w-full mt-2 py-2 rounded-lg'
                )

            # Gripper control & path planning in one row
            with ui.row().classes('w-full gap-4'):
                # Gripper control
                with ui.card().classes('w-1/2 p-4'):
                    ui.label("🛠 Gripper Control").classes('text-xl font-bold mb-2')
                    with ui.row().classes('justify-center gap-4'):
                        ui.button("Open Gripper", on_click=lambda: utils.open_gripper(Arctos)).classes('bg-yellow-500 text-white px-4 py-2 rounded-lg')
                        ui.button("Close Gripper", on_click=lambda: utils.close_gripper(Arctos)).classes('bg-orange-500 text-white px-4 py-2 rounded-lg')

                # Path planning
                with ui.card().classes('w-1/2 p-4'):
                    ui.label("📌 Path Planning").classes('text-xl font-bold text-center mb-2')
                    with ui.grid(columns=2).classes('gap-4'):
                        ui.button("Save Pose", on_click=lambda: utils.save_pose(planner, robot)).classes('bg-blue-700 text-white px-4 py-2 rounded-lg')
                        ui.button("Load Program", on_click=lambda: utils.load_program(planner)).classes('bg-green-700 text-white px-4 py-2 rounded-lg')
                        ui.button("Save Program", on_click=lambda: utils.save_program(planner)).classes('bg-indigo-700 text-white px-4 py-2 rounded-lg')
                        ui.button("Execute Program", on_click=lambda: utils.execute_path(planner, robot)).classes('bg-red-700 text-white px-4 py-2 rounded-lg')


        # --- RIGHT SECTION: MeshCat & Console ---
        with ui.column():
            # MeshCat Visualization (now full width!)
            with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg flex-grow'):
                ui.label("🖥️ 3D Visualization (MeshCat)").classes('text-xl font-bold mb-2')
                ui.html(f'''<iframe src="{MESH_CAT_URL}" style="width: 100%; height: 500px; border: none;"></iframe>''').classes('w-full')
                
                # 🌟 SWITCH for keyboard control
                with ui.row().classes('w-full justify-center mt-4'):
                    keyboard_control_switch = ui.switch("🎮 Enable Keyboard Control", value=False)
                    keyboard_control_switch.on('click', utils.toggle_keyboard_control)

            # RPY Control
            with ui.card().classes('w-full p-4 mt-2'):
                ui.label("🔄 End-Effector Orientation (RPY)").classes('text-xl font-bold mb-2')
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    ee_orientation_labels = {axis: ui.label(f"{axis}: 0.00°").classes('text-lg w-full text-center') for axis in ["Roll", "Pitch", "Yaw"]}
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    ee_orientation_inputs = {axis: ui.number(label=f"{axis} (°)").classes('w-full') for axis in ["Roll", "Pitch", "Yaw"]}
                ui.button("✅ Set End-Effector Orientation", on_click=set_ee_orientation_from_input).classes(
                    'bg-blue-500 text-white w-full mt-2 py-2 rounded-lg'
                )

            # Konsolen-Output
            with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg mt-4'):
                ui.label("📟 Console-Output").classes('text-xl font-bold mb-2')
                console_output = ui.log(max_lines=10).classes('border p-2 h-48 bg-gray-900 text-white')

    # UI starten
    ui.timer(0.5, lambda: utils.update_joint_states(robot, joint_positions))
    #ui.timer(0.5, lambda: robot.display(robot.q))  # Sicherstellen, dass immer der aktuelle Stand animiert wird
    ui.timer(0.5, lambda: utils.update_ee_postion(robot, ee_position_labels))
    ui.timer(0.5, live_update_ee_orientation)
    #utils.initilize_current_joint_states(robot, Arctos)