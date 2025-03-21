from nicegui import ui

# Import local modules
import homing
import utils


MESH_CAT_URL = "http://127.0.0.1:7000/static/"

def create(Arctos, robot, planner):
    """
    Creates the control page for robot operation.
    """
    ui.label("Control").classes('text-3xl font-bold text-center mb-4')
    # 🎮 Add keyboard listener directly in `create()`
    ui.keyboard(lambda event: utils.on_key(event, robot, Arctos))
    # Layout with two columns: Control on the left | Visualization & Console on the right
    with ui.grid(columns=2).classes('w-full gap-4'):

        # --- LEFT SECTION: Control ---
        with ui.column().classes('w-full'):
            # # 🌟 Button to initialize the robot 
            # ui.button("🔄 Initialize Robot", on_click=initialize_robot).classes('bg-blue-500 text-white w-full mt-2 py-2 rounded-lg')            
            # Home and Sleep Pose buttons
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("▶️ Start Movement", on_click=lambda: utils.run_move_can(robot, Arctos)).classes('bg-red-500 text-white w-full mt-2 py-2 rounded-lg')
            
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("Reset to Zero", on_click=lambda: utils.reset_to_zero_position(robot)).classes('bg-gray-700 text-white px-4 py-2 rounded-lg mt-2')

            # --- Expandable Joint Control Section ---
            with ui.expansion("🦾 Joint Control", icon="settings", value=False).classes('w-full border-2 border-gray-400'):
                
                ui.label("View and set the joint angles.").classes('text-gray-600 mb-2')

                # Display current joint positions (Read-Only Labels)
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    joint_positions = [ui.label(f"Joint {i+1}: 0.0°").classes('text-lg w-full text-center') for i in range(6)]

                # Input fields for setting new joint angles
                with ui.grid(columns=3).classes('gap-4 w-full'):
                    new_joint_inputs = [ui.number(label=f"Joint {i+1} (°)").classes('w-full') for i in range(6)]

                # Button to Set Joint Angles
                ui.button("✅ Set Joint Angles", on_click=lambda: utils.set_joint_angles_from_gui(robot, new_joint_inputs)).classes(
                    'bg-green-500 text-white w-full mt-2 py-2 rounded-lg'
                )
            with ui.expansion('End-Effector', value=False).classes('w-full border-2 border-gray-400'):
                # --- Expandable End-Effector Position Section ---
                with ui.expansion("End-Effector Position", icon="location_on", value=False).classes('w-full border-2 border-gray-400'):
                    
                    ui.label("View and set the end-effector position.").classes('text-gray-600 mb-2')

                    # Display End-Effector Position (Read-Only Labels)
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_position_labels = {axis: ui.label(f"{axis}: 0.00 m").classes('text-lg w-full text-center') for axis in ["X", "Y", "Z"]}

                    # Input Fields for Setting New Cartesian Position
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_position_inputs = {axis: ui.number(label=f"{axis} (m)").classes('w-full') for axis in ["X", "Y", "Z"]}

                    # Button to Set End-Effector Position
                    ui.button("✅ Set End-Effector Position", on_click=lambda: utils.set_ee_position_from_input(robot, ee_position_inputs)).classes(
                        'bg-green-500 text-white w-full mt-2 py-2 rounded-lg'
                    )

                # --- RPY Control (Expandable) ---
                with ui.expansion('🔄 End-Effector Orientation (RPY)', icon='rotate_right', value=False).classes('w-full border-2 border-gray-400'):
                    ui.label("Set and monitor the end-effector orientation").classes('text-lg font-semibold mb-2')

                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_orientation_labels = {axis: ui.label(f"{axis}: 0.00°").classes('text-lg w-full text-center') for axis in ["Roll", "Pitch", "Yaw"]}

                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_orientation_inputs = {axis: ui.number(label=f"{axis} (°)").classes('w-full') for axis in ["Roll", "Pitch", "Yaw"]}

                    ui.button("✅ Set End-Effector Orientation", on_click=lambda: utils.set_ee_orientation_from_input(robot, ee_orientation_inputs)).classes(
                        'bg-blue-500 text-white w-full mt-2 py-2 rounded-lg'
                    )

            # Gripper Control inside an expandable accordion
            with ui.expansion("🛠 Gripper Control", icon="hand", value=False).classes('w-full border-2 border-gray-400'):
                ui.label("Control the gripper's movement.").classes('text-gray-600 mb-2')
                
                with ui.row().classes('justify-center gap-4'):
                    ui.button("Open Gripper", on_click=lambda: utils.open_gripper(Arctos)).classes('bg-yellow-500 text-white px-4 py-2 rounded-lg')
                    ui.button("Close Gripper", on_click=lambda: utils.close_gripper(Arctos)).classes('bg-orange-500 text-white px-4 py-2 rounded-lg')

            # --- Expandable Path Planning Section ---
            with ui.expansion("📌 Path Planning", icon="map", value=False).classes('w-full border-2 border-gray-400'):
                
                ui.label("Manage and execute path planning tasks.").classes('text-gray-600 text-center mb-2')

                with ui.row().classes('w-full'):
                    pose_container = ui.column().classes('w-full')
                    utils.update_pose_table(planner, robot, pose_container)
                    ui.button("Save Pose", on_click=lambda: (utils.save_pose(planner, robot), utils.update_pose_table(planner, robot, pose_container))).classes('bg-blue-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Load Program", on_click=lambda: (utils.load_program(planner), utils.update_pose_table(planner, robot, pose_container))).classes('bg-green-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Save Program", on_click=lambda: utils.save_program(planner)).classes('bg-indigo-700 text-white px-4 py-2 rounded-lg')
                    ui.button("Execute Program", on_click=lambda: utils.execute_path(planner, robot, Arctos)).classes('bg-red-700 text-white px-4 py-2 rounded-lg')
                    


            ui.button("🏠 Move to Home Pose", on_click=lambda: homing.move_to_zero_pose(Arctos)).classes('bg-purple-500 text-white px-4 py-2 rounded-lg')
            ui.button("💤 Move to Sleep Pose", on_click=lambda: homing.move_to_sleep_pose(Arctos)).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')


        # --- RIGHT SECTION: MeshCat & Console ---
        with ui.column().classes('w-full'):
            # MeshCat Visualization (now full width!)
            with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg flex-grow'):
                ui.label("🖥️ 3D Visualization").classes('text-xl font-bold mb-2')
                ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 500px; border: none;"></iframe>''').classes('w-full')
                
                # 🌟 SWITCH for keyboard control
                with ui.row().classes('w-full justify-center mt-4'):
                    keyboard_control_switch = ui.switch("🎮 Enable Keyboard Control", value=False)
                    keyboard_control_switch.on('click', utils.toggle_keyboard_control)

    # UI starten
    ui.timer(0.25, lambda: utils.update_joint_states(robot, joint_positions))
    ui.timer(0.25, lambda: utils.live_update_ee_postion(robot, ee_position_labels))
    ui.timer(0.25, lambda: utils.live_update_ee_orientation(robot, ee_orientation_labels))
    ui.timer(0.2, lambda: utils.threaded_initialize_current_joint_states(robot, Arctos))
    #utils.initialize_current_joint_states(robot, Arctos)