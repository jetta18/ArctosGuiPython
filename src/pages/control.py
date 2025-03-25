from nicegui import ui
from utils import utils
from core import homing

# Import local modules

MESH_CAT_URL = "http://127.0.0.1:7000/static/"

def create(Arctos, robot, planner):
    """
    Creates the control page for robot operation.
    """

    ui.label("Control Page").classes('text-3xl font-bold text-center mb-4')

    with ui.card().classes('w-full bg-blue-50 border border-blue-300 rounded-2xl shadow-md p-4 mb-6'):
        ui.label("Live Joint-States").classes('text-lg font-semibold text-blue-800 mb-2 text-center')
        
        with ui.grid(columns=6).classes('w-full'):
            joint_positions_encoder = [
                ui.label(f"J{i+1}: --.--°")
                .classes('text-sm text-center font-mono text-blue-900 bg-white rounded-lg px-2 py-1 border border-blue-200 shadow-sm') 
                for i in range(6)
            ]

    # 🎮 Add keyboard listener directly in `create()`
    ui.keyboard(lambda event: utils.on_key(event, robot, Arctos))
    # Layout with two columns: Control on the left | Visualization & Console on the right
    with ui.grid(columns=2).classes('w-full gap-4'):

        # --- LEFT SECTION: Control ---
        with ui.column().classes('w-full'):
                        
            # Home and Sleep Pose buttons
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("▶️ Start Movement", on_click=lambda: utils.run_move_can(robot, Arctos)) \
                .tooltip("Execute the currently set joint angles on the physical robot") \
                .classes('bg-red-500 text-white w-full mt-2 py-2 rounded-lg')
            
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("Reset to Zero", on_click=lambda: utils.reset_to_zero_position(robot)) \
                .tooltip("Move all joints to 0° without using homing or encoders") \
                .classes('bg-gray-700 text-white px-4 py-2 rounded-lg mt-2')

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
                ui.button("✅ Set Joint Angles", on_click=lambda: utils.set_joint_angles_from_gui(robot, new_joint_inputs)) \
                    .tooltip("Send entered joint angles to the robot using forward kinematics") \
                    .classes('bg-green-500 text-white w-full mt-2 py-2 rounded-lg')

            with ui.expansion('End-Effector', value=False).classes('w-full border-2 border-gray-400'):

                # --- End-Effector Position Section ---
                with ui.expansion("End-Effector Position", icon="location_on", value=False).classes('w-full border-2 border-gray-400'):
                    ui.label("View and set the end-effector position.").classes('text-gray-600 mb-2')

                    # Read-only labels showing current XYZ position
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_position_labels = {
                            axis: ui.label(f"{axis}: 0.00 m").classes('text-lg w-full text-center')
                            for axis in ["X", "Y", "Z"]
                        }

                    # Input fields for XYZ
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_position_inputs = {
                            axis: ui.number(label=f"{axis} (m)").classes('w-full')
                            for axis in ["X", "Y", "Z"]
                        }

                # --- End-Effector Orientation (RPY) Section ---
                with ui.expansion('🔄 End-Effector Orientation (RPY)', icon='rotate_right', value=False).classes('w-full border-2 border-gray-400'):
                    ui.label("Set and monitor the end-effector orientation").classes('text-lg font-semibold mb-2')

                    # Read-only labels showing current RPY
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_orientation_labels = {
                            axis: ui.label(f"{axis}: 0.00°").classes('text-lg w-full text-center')
                            for axis in ["Roll", "Pitch", "Yaw"]
                        }

                    # Input fields for RPY
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        ee_orientation_inputs = {
                            axis: ui.number(label=f"{axis} (°)").classes('w-full')
                            for axis in ["Roll", "Pitch", "Yaw"]
                        }

                # --- Orientation Switch and Combined Button ---
                with ui.row().classes('justify-center mt-2'):
                    use_orientation_switch = ui.switch("🔄 Include Orientation (RPY)", value=False)

                ui.button("🚀 Set End-Effector Pose", on_click=lambda:
                    utils.set_ee_pose_from_input(
                        robot,
                        ee_position_inputs,
                        ee_orientation_inputs,
                        use_orientation_switch.value
                    )
                ).tooltip("Uses inverse kinematics to move the end-effector to the specified position and orientation") \
                .classes('bg-teal-600 text-white w-full mt-2 py-2 rounded-lg')



            # Gripper Control inside an expandable accordion
            with ui.expansion("🛠 Gripper Control", icon="hand", value=False).classes('w-full border-2 border-gray-400'):
                ui.label("Control the gripper's movement.").classes('text-gray-600 mb-2')
                
                with ui.row().classes('justify-center gap-4'):
                    ui.button("Open Gripper", on_click=lambda: utils.open_gripper(Arctos)) \
                        .tooltip("Send command to open the robot gripper") \
                        .classes('bg-yellow-500 text-white px-4 py-2 rounded-lg')

                    ui.button("Close Gripper", on_click=lambda: utils.close_gripper(Arctos)) \
                        .tooltip("Send command to close the robot gripper") \
                        .classes('bg-orange-500 text-white px-4 py-2 rounded-lg')

            # --- Expandable Path Planning Section ---
            with ui.expansion("📌 Path Planning", icon="map", value=False).classes('w-full border-2 border-gray-400'):
                
                ui.label("Manage and execute path planning tasks.").classes('text-gray-600 text-center mb-2')

                with ui.row().classes('w-full'):
                    pose_container = ui.column().classes('w-full')
                    utils.update_pose_table(planner, robot, pose_container)
                    ui.button("Save Pose", on_click=lambda: (
                        utils.save_pose(planner, robot),
                        utils.update_pose_table(planner, robot, pose_container))
                    ).tooltip("Store the robot's current pose for later use") \
                    .classes('bg-blue-700 text-white px-4 py-2 rounded-lg')

                    ui.button("Load Program", on_click=lambda: utils.load_program(planner, pose_container, robot)) \
                        .tooltip("Load a previously saved sequence of poses") \
                        .classes('bg-green-700 text-white px-4 py-2 rounded-lg')

                    ui.button("Save Program", on_click=lambda: utils.save_program(planner)) \
                        .tooltip("Save all recorded poses into a named program file") \
                        .classes('bg-indigo-700 text-white px-4 py-2 rounded-lg')

                    ui.button("Execute Program", on_click=lambda: utils.execute_path(planner, robot, Arctos)) \
                        .tooltip("Run the full program on the robot in real-time") \
                        .classes('bg-red-700 text-white px-4 py-2 rounded-lg')


            ui.button("🏠 Move to Home Pose", on_click=lambda: homing.move_to_zero_pose(Arctos)) \
                .tooltip("Send robot to predefined 'home' configuration") \
                .classes('bg-purple-500 text-white px-4 py-2 rounded-lg')

            ui.button("💤 Move to Sleep Pose", on_click=lambda: homing.move_to_sleep_pose(Arctos)) \
                .tooltip("Send robot to safe resting position (sleep pose)") \
                .classes('bg-gray-500 text-white px-4 py-2 rounded-lg')


        # --- RIGHT SECTION: MeshCat & Console ---
        with ui.column().classes('w-full'):
            # MeshCat Visualization (now full width!)
            with ui.card().classes('w-full p-4 bg-gray-100 border border-gray-300 rounded-lg flex-grow'):
                ui.label("🖥️ 3D Visualization").classes('text-xl font-bold mb-2')
                ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 500px; border: none;"></iframe>''').classes('w-full')
                
                with ui.row().classes('w-full justify-center items-start mt-4 gap-12'):
                    
                    # 🎮 Keyboard Control Switch
                    with ui.column().classes("items-center"):
                        ui.label("🎮 Keyboard Control").classes("text-sm font-medium text-gray-700 mb-1")
                        keyboard_control_switch = ui.switch("", value=False)
                        keyboard_control_switch.on('click', utils.toggle_keyboard_control)

                    # 🪜 Step Size Slider with Label + Tooltip
                    with ui.column().classes("items-center"):
                        with ui.row().classes("items-center gap-1"):
                            ui.label("Step Size (m)").classes("text-sm font-medium text-gray-700")
                            ui.icon("info").tooltip("Determines how far the robot moves per key press (W/A/S/D/Q/E).")

                        utils.step_size_input = ui.slider(
                            min=0.0005,
                            max=0.02,
                            value=0.002,
                            step=0.0005
                        ).props('label-always').classes('w-64')




    # UI starten
    ui.timer(0.25, lambda: utils.update_joint_states(robot, joint_positions))
    ui.timer(0.25, lambda: utils.update_joint_states_encoder(robot, joint_positions_encoder))
    ui.timer(0.25, lambda: utils.live_update_ee_postion(robot, ee_position_labels))
    ui.timer(0.25, lambda: utils.live_update_ee_orientation(robot, ee_orientation_labels))
    ui.timer(0.3, lambda: utils.threaded_initialize_current_joint_states(robot, Arctos))
    #utils.initialize_current_joint_states(robot, Arctos)