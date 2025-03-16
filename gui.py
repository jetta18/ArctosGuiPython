from nicegui import ui
import datetime
import numpy as np

# Import local modules
from arctos_controller import ArctosController
from path_planning import PathPlanner
import homing
import utils
from ArctosPinocchio import ArctosPinocchioRobot


MESH_CAT_URL = "http://127.0.0.1:7000/static/"


Arctos = ArctosController()
robot = ArctosPinocchioRobot()
planner = PathPlanner()

utils.initialize_keyboard_listeners(robot, Arctos)
utils.initilize_current_joint_states(robot, Arctos)

def live_update_ee_orientation():
    """Liest die aktuelle Endeffektor-Orientierung aus `robot` und aktualisiert die UI in Echtzeit."""
    #utils.update_ee_orientation(robot, ee_orientation_labels)

def set_ee_orientation_from_input():
    """Liest die Eingaben für Roll, Pitch, Yaw aus der UI und bewegt den Roboter zur neuen Orientierung."""
    #utils.set_orientation_values_from_gui(robot, ee_orientation_inputs)

# --- UI START ---
ui.label("🤖 Arctos Robot Control").classes('text-3xl font-bold text-center mb-4')

# Layout mit 2 Spalten: Steuerung links | Visualisierung & Konsole rechts
with ui.grid(columns=2).classes('gap-4'):

    # --- LINKER BEREICH: Steuerung ---
    with ui.column():

        # Home- und Sleep-Pose Knöpfe
        with ui.row().classes('w-full justify-center mt-4 gap-4'):
            ui.button("🏠 Fahre zur Home-Pose", on_click= lambda: homing.move_to_zero_pose(Arctos)).classes('bg-purple-500 text-white px-4 py-2 rounded-lg')
            ui.button("💤 Fahre zur Sleep-Pose", on_click= lambda: homing.move_to_sleep_pose(Arctos)).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')
            # --- Neuer Button zum Starten der Bewegung ---
            ui.button("▶️ Bewegung starten", on_click= lambda: utils.run_move_can(robot, Arctos)).classes('bg-red-500 text-white w-full mt-2 py-2 rounded-lg')
            # --- Toggle Keyboard Control Button ---
        # --- Gelenksteuerung in der UI ---
        with ui.card().classes('w-full p-4'):
            ui.label("🦾 Gelenksteuerung").classes('text-xl font-bold mb-2')
            
            with ui.grid(columns=3).classes('gap-4 w-full'):
                joint_positions = [ui.label(f"Gelenk {i+1}: 0.0°").classes('text-lg w-full text-center') for i in range(6)]
            with ui.grid(columns=3).classes('gap-4 w-full'):
                new_joint_inputs = [ui.number(label=f"Gelenk {i+1} (°)").classes('w-full') for i in range(6)]  # Eingabefelder
            
            # Neuer Button zum Setzen der Gelenkwinkel
            ui.button("✅ Gelenkwinkel setzen", on_click= lambda: utils.set_joint_angles_from_gui(robot, new_joint_inputs)).classes(
                'bg-green-500 text-white w-full mt-2 py-2 rounded-lg'
            )
        # --- Kartesische Position des Endeffektors ---
        with ui.card().classes('w-full p-4 mt-2'):
            ui.label("📍 Endeffektor-Position").classes('text-xl font-bold mb-2')
            
            with ui.grid(columns=3).classes('gap-4 w-full'):
                ee_position_labels = {axis: ui.label(f"{axis}: 0.00 mm").classes('text-lg w-full text-center') for axis in ["X", "Y", "Z"]}
            with ui.grid(columns=3).classes('gap-4 w-full'):
                ee_position_inputs = {axis: ui.number(label=f"{axis} (mm)").classes('w-full') for axis in ["X", "Y", "Z"]}
            
            # Button zum Setzen der Endeffektor-Position
            ui.button("✅ Endeffektor-Position setzen", on_click= lambda: utils.set_cartesian_values_from_gui(robot, ee_position_inputs)).classes(
                'bg-green-500 text-white w-full mt-2 py-2 rounded-lg'
            )

        # Greifersteuerung & Pfadplanung in einer Zeile
        with ui.row().classes('w-full gap-4'):
            # Greifersteuerung
            with ui.card().classes('w-1/2 p-4'):
                ui.label("🛠 Greifersteuerung").classes('text-xl font-bold mb-2')
                with ui.row().classes('justify-center gap-4'):
                    ui.button("Greifer öffnen", on_click= lambda: utils.open_gripper(Arctos)).classes('bg-yellow-500 text-white px-4 py-2 rounded-lg')
                    ui.button("Greifer schließen", on_click= lambda: utils.close_gripper(Arctos)).classes('bg-orange-500 text-white px-4 py-2 rounded-lg')

            # Pfadplanung
            with ui.card().classes('w-1/2 p-4'):
                ui.label("📌 Pfadplanung").classes('text-xl font-bold text-center mb-2')
                with ui.grid(columns=2).classes('gap-4'):
                    ui.button("Save Pose", on_click= lambda: utils.save_pose(planner, robot)).classes('bg-blue-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Load Program", on_click= lambda: utils.load_program(planner)).classes('bg-green-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Save Program", on_click= lambda: utils.save_program(planner)).classes('bg-indigo-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Execute Program", on_click= lambda: utils.execute_path(planner, robot)).classes('bg-red-700 text-white px-4 py-2 rounded-lg')


    # --- RECHTER BEREICH: MeshCat & Konsole ---
    with ui.column():
        # MeshCat Visualisierung (jetzt volle Breite!)
        with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg flex-grow'):
            ui.label("🖥️ 3D-Visualisierung (MeshCat)").classes('text-xl font-bold mb-2')
            ui.html(f'''
                <iframe src="{MESH_CAT_URL}" style="width: 100%; height: 500px; border: none;"></iframe>
            ''').classes('w-full')
            
            # Button in die Mitte setzen
            with ui.row().classes('w-full justify-center mt-4'):
                ui.button("🎮 Toggle Keyboard Control", on_click=utils.toggle_keyboard_control).classes('bg-blue-500 text-white px-4 py-2 rounded-lg')

        # Neue RPY-Steuerung
        with ui.card().classes('w-full p-4 mt-2'):
            ui.label("🔄 Endeffektor-Orientierung (RPY)").classes('text-xl font-bold mb-2')
            with ui.grid(columns=3).classes('gap-4 w-full'):
                ee_orientation_labels = {axis: ui.label(f"{axis}: 0.00°").classes('text-lg w-full text-center') for axis in ["Roll", "Pitch", "Yaw"]}
            with ui.grid(columns=3).classes('gap-4 w-full'):
                ee_orientation_inputs = {axis: ui.number(label=f"{axis} (°)").classes('w-full') for axis in ["Roll", "Pitch", "Yaw"]}
            ui.button("✅ Endeffektor-Orientierung setzen", on_click=set_ee_orientation_from_input).classes(
                'bg-blue-500 text-white w-full mt-2 py-2 rounded-lg'
            )

        # Konsolen-Output
        with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg mt-4'):
            ui.label("📟 Konsolen-Output").classes('text-xl font-bold mb-2')
            console_output = ui.log(max_lines=10).classes('border p-2 h-48 bg-gray-900 text-white')

# UI starten
ui.timer(0.5, lambda: utils.update_joint_states(robot, joint_positions))
#ui.timer(0.5, lambda: robot.display(robot.q))  # Sicherstellen, dass immer der aktuelle Stand animiert wird
ui.timer(0.5, lambda: utils.update_ee_postion(robot, ee_position_labels))
ui.timer(0.5, live_update_ee_orientation)

ui.run(reload=False)
