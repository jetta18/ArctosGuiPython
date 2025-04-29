"""
This module defines the control page for the Arctos Robot GUI.

It provides functionality for controlling the robot's movement, viewing its current state,
and executing path planning tasks.
"""
from nicegui import ui
from utils import utils
from core import homing

# Define the URL for the MeshCat visualization server.
MESH_CAT_URL = "http://127.0.0.1:7000/static/"


def create(Arctos, robot, planner, settings_manager) -> None:
    """
    Creates the control page for the Arctos Robot GUI.

    This function sets up the layout and functionality of the control page,
    including live updates, joint control, end-effector control, path planning,
    gripper control, and a 3D visualization.

    Args:
        Arctos: The ArctosController instance for robot communication.
        robot: The ArctosPinocchioRobot instance for robot kinematics.
        planner: The PathPlanner instance for path planning.
        settings_manager: An object that manages the GUI settings.

    Returns:
        None
    """

    # Apply UI Theme on page init
    # Check if the user has set the dark theme
    if settings_manager.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    # page header
    ui.label("Control Page").classes('text-3xl font-bold text-left mt-2 mb-2 px-2')



    def apply_speed(val):
        try:
            val = float(val)
        except (TypeError, ValueError):
            ui.notify('Please enter a valid number for speed scale', color='negative')
            return
        if not (0.1 <= val <= 2.0):
            ui.notify('Please enter a value between 0.1 and 2.0', color='negative')
            return
        utils.set_speed_scale(val)
        settings_manager.set('speed_scale', val)
        ui.notify(f'Speed scale set to {int(val*100)} %', color='positive')



    
    # Conditional UI Timers
    # Check if the user enabled live joint updates
    if settings_manager.get("enable_live_joint_updates", True):
        # --- Modern Joint Control Card: Live Joint-States ---
        with ui.expansion('Joint Control', icon='tune', value=False).classes('w-[600px] max-w-full bg-gradient-to-br from-blue-50 to-cyan-100 border border-blue-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
            with ui.row().classes('items-center mb-2'):
                ui.icon('sensors').classes('text-2xl text-blue-700 mr-2')
                ui.label("Live Joint-States").classes('text-2xl font-bold text-blue-900 tracking-wide')
            ui.separator().classes('my-2')
            # create a grid with 6 labels to display the current joint values
            with ui.grid(columns=6).classes('w-full'):
                joint_positions_encoder = [
                    ui.label(f"J{i+1}: --.--°")
                    .classes(
                        'text-base text-center font-mono text-blue-900 bg-white rounded-lg px-3 py-2 border border-blue-200 shadow-sm'
                    )
                    for i in range(6)
                ]

    # --- ENHANCED KEYBOARD CONTROL INTEGRATION ---
    # Setup the enhanced keyboard controller (singleton)
    # Provide a notify_fn for UI notifications
    def notify_fn(msg, color=None):
        ui.notify(msg, color=color)
    # Step size slider will be created below and attached
    step_size_slider = None  # placeholder
    # Setup controller instance (step_size_slider will be set after creation)
    keyboard_ctrl = utils.setup_keyboard_controller(robot, Arctos, None, notify_fn)
    # Attach NiceGUI keyboard event
    ui.keyboard(lambda event: utils.on_key(event, robot, Arctos))
    # Layout with two columns: Control on the left | Visualization & Console on the right
    with ui.row().classes('w-full h-[calc(100vh-60px)] gap-2 items-stretch'):

        # --- LEFT SECTION: Control ---
        with ui.column().classes('flex-2 min-w-0 gap-2 items-stretch'):
            expansion_common = 'w-[600px] max-w-full bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300'
            # --- Modern Speed Scale Section (Styled Expansion) ---
            with ui.expansion('Speed Scale', icon='speed', value=False).classes(expansion_common).props('expand-icon="expand_more" id=speed-scale-section'):
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.icon('speed').classes('text-blue-600')
                    ui.label('Speed Scale').classes('text-lg font-semibold text-blue-900 tracking-wide')
                    ui.icon('help').tooltip(
                        'Scales the overall robot movement speed.\n1.0 = 100 %\nUse the slider or enter a value.'
                    ).classes('text-blue-400 cursor-help')
                speed_val = settings_manager.get('speed_scale', 1.0)
                with ui.row().classes('items-center gap-3'):
                    speed_slider = ui.slider(
                        min=0.1, max=2.0, value=speed_val, step=0.01
                    ).props('dense label-always color=primary').classes('w-52 hover:scale-105 transition-transform')
                    speed_display = ui.label(f"{int(speed_val*100)} %") \
                        .classes('font-mono text-lg text-blue-800 ml-2')
                    speed_input = ui.number(
                        value=speed_val, min=0.1, max=2.0, step=0.01, format='%.2f'
                    ).classes('w-16 ml-2 border-blue-300 rounded')
                    ui.button('Apply', on_click=lambda: apply_speed(speed_slider.value)) \
                        .props('color=primary dense').classes('ml-3 px-4 py-1 rounded-lg text-white font-semibold shadow hover:bg-blue-700 transition-colors')
                def safe_percent(val):
                    try:
                        num = float(val)
                        return f"{int(round(num * 100))} %"
                    except Exception:
                        return "-- %"
                speed_slider.on('update:model-value', lambda e: [
                    speed_input.set_value(e.args),
                    speed_display.set_text(safe_percent(e.args))
                ])
                speed_input.on('update:model-value', lambda e: [
                    speed_slider.set_value(e.args),
                    speed_display.set_text(safe_percent(e.args))
                ])
            # --- End Speed Scale Section (Styled Expansion) ---

            # Home and Sleep Pose buttons
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("Start Movement", on_click=lambda: utils.run_move_can(robot, Arctos, settings_manager)) \
                .tooltip("Execute the currently set joint angles on the physical robot") \
                .classes('bg-red-500 text-white w-full mt-2 py-2 rounded-lg')
            
            with ui.row().classes('w-full justify-center mt-4 gap-4'):
                ui.button("Reset to Zero", on_click=lambda: utils.reset_to_zero_position(robot)) \
                .tooltip("Move all joints to 0° without using homing or encoders") \
                .classes('bg-gray-700 text-white px-4 py-2 rounded-lg mt-2')

            # --- Modern Joint Control Card (Styled Expansion) ---
            with ui.expansion('Joint Control', icon='360', value=False).classes('w-[600px] max-w-full bg-gradient-to-br from-blue-50 to-cyan-100 border border-blue-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
                with ui.row().classes('items-center mb-2'):
                    ui.icon('360').classes('text-2xl text-blue-700 mr-2')
                    ui.label('Joint Control').classes('text-2xl font-bold text-blue-900 tracking-wide')
                ui.separator().classes('my-2')
                ui.label("View and set the joint angles.").classes('text-gray-600 mb-4')
                # Display current joint positions (Read-Only Labels)
                with ui.grid(columns=3).classes('gap-4 w-full mb-2'):
                    joint_positions = [
                        ui.label(f"Joint {i+1}: 0.0°").classes('text-lg w-full text-center bg-white border border-blue-200 rounded-lg py-2 shadow-sm font-mono text-blue-900') for i in range(6)
                    ]
                # Input fields for setting new joint angles
                with ui.grid(columns=3).classes('gap-4 w-full mb-2'):
                    new_joint_inputs = [ui.number(label=f"Joint {i+1} (°)").classes('w-full border-blue-200 rounded-lg') for i in range(6)]
                # Button to Set Joint Angles
                ui.button("Set Joint Angles", on_click=lambda: utils.set_joint_angles_from_gui(robot, new_joint_inputs)) \
                    .tooltip("Send entered joint angles to the robot using forward kinematics") \
                    .classes('bg-blue-600 text-white w-full mt-2 py-2 rounded-lg shadow hover:bg-blue-800')
            # --- End Joint Control Card (Styled Expansion) ---

            # --- Modern End-Effector Control Expansion ---
            with ui.expansion('End-Effector Control', icon='open_with', value=False).classes('w-[600px] max-w-full bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
                with ui.row().classes('items-center mb-2'):
                    ui.icon('open_with').classes('text-2xl text-purple-700 mr-2')
                    ui.label('End-Effector Control').classes('text-2xl font-bold text-purple-900 tracking-wide')
                ui.separator().classes('my-2')
                # --- Live Readout Row ---
                with ui.row().classes('gap-2 mb-4 flex-wrap items-center justify-center'):
                    ee_position_labels = {}
                    for axis in ["X", "Y", "Z"]:
                        ee_position_labels[axis] = ui.label(f"{axis}: 0.00 m").classes('px-2 py-1 rounded bg-blue-100 text-blue-900 font-mono')
                    ui.label('|').classes('mx-2 text-gray-400')
                    ee_orientation_labels = {}
                    for axis in ["Roll", "Pitch", "Yaw"]:
                        ee_orientation_labels[axis] = ui.label(f"{axis}: 0.00°").classes('px-2 py-1 rounded bg-purple-100 text-purple-900 font-mono')
                # --- Segmented Mode Selector ---
                mode = ui.toggle(["Position Only", "Position + Orientation", "Orientation Only"], value="Position + Orientation") \
                    .classes('w-full my-4')
                # --- Inputs Area ---
                ee_position_inputs = {axis: None for axis in ["X", "Y", "Z"]}
                ee_orientation_inputs = {axis: None for axis in ["Roll", "Pitch", "Yaw"]}
                input_container = ui.element('div').classes('w-full')
                def update_inputs():
                    # Clear and re-create input fields based on mode
                    nonlocal ee_position_inputs, ee_orientation_inputs
                    input_container.clear()
                    for axis in ["X", "Y", "Z"]:
                        ee_position_inputs[axis] = None
                    for axis in ["Roll", "Pitch", "Yaw"]:
                        ee_orientation_inputs[axis] = None
                    if mode.value in ("Position Only", "Position + Orientation"):
                        with input_container:
                            with ui.row().classes('gap-4 w-full mb-2'):
                                for axis in ["X", "Y", "Z"]:
                                    ee_position_inputs[axis] = ui.number(label=f"{axis} (m)", format="%.3f").props('dense') \
                                        .tooltip(f"Target {axis} coordinate in meters.") \
                                        .classes('w-32 rounded border-blue-200')
                    if mode.value in ("Position + Orientation", "Orientation Only"):
                        with input_container:
                            with ui.row().classes('gap-4 w-full mb-2'):
                                for axis in ["Roll", "Pitch", "Yaw"]:
                                    ee_orientation_inputs[axis] = ui.number(label=f"{axis} (°)", format="%.1f").props('dense') \
                                        .tooltip(f"Target {axis} angle in degrees.") \
                                        .classes('w-32 rounded border-purple-200')
                # Initial input render
                update_inputs()
                # Re-render on mode change
                mode.on('update:model-value', lambda e: update_inputs())
                # Place the container in the UI
                input_container.move()                # --- Action Buttons ---
                last_action_label = ui.label("").classes('block mt-2 text-sm text-gray-600')
                def set_pose():
                    try:
                        utils.set_ee_pose_from_input(robot, ee_position_inputs, ee_orientation_inputs, True)
                        last_action_label.set_text("✅ End-Effector moved to position and orientation.")
                        last_action_label.classes('text-green-700')
                    except Exception as e:
                        last_action_label.set_text(f"❌ {str(e)}")
                        last_action_label.classes('text-red-700')
                def set_position():
                    try:
                        utils.set_ee_position_from_input(robot, ee_position_inputs)
                        last_action_label.set_text("✅ End-Effector moved to position.")
                        last_action_label.classes('text-green-700')
                    except Exception as e:
                        last_action_label.set_text(f"❌ {str(e)}")
                        last_action_label.classes('text-red-700')
                def set_orientation():
                    try:
                        utils.set_ee_orientation_from_input(robot, ee_orientation_inputs)
                        last_action_label.set_text("✅ End-Effector orientation updated.")
                        last_action_label.classes('text-green-700')
                    except Exception as e:
                        last_action_label.set_text(f"❌ {str(e)}")
                        last_action_label.classes('text-red-700')
                with ui.row().classes('gap-4 w-full mt-4 justify-center'):
                    btn_pos = ui.button("📍 Set Position", on_click=set_position) \
                        .tooltip("Move to XYZ position only (keeps orientation).") \
                        .classes('bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-800')
                    btn_pose = ui.button("🚀 Set Position + Orientation", on_click=set_pose) \
                        .tooltip("Move to XYZ + RPY using inverse kinematics.") \
                        .classes('bg-teal-600 text-white px-4 py-2 rounded-lg shadow hover:bg-teal-800')
                    btn_ori = ui.button("🎯 Set Orientation Only", on_click=set_orientation) \
                        .tooltip("Update only orientation (RPY) at current position.") \
                        .classes('bg-purple-700 text-white px-4 py-2 rounded-lg shadow hover:bg-purple-900')
                    # Show/hide buttons based on mode
                    def update_button_visibility():
                        btn_pos.set_visibility(mode.value == "Position Only")
                        btn_pose.set_visibility(mode.value == "Position + Orientation")
                        btn_ori.set_visibility(mode.value == "Orientation Only")
                    update_button_visibility()
                    mode.on('update:model-value', lambda e: update_button_visibility())
                # --- Last Action Status ---
                last_action_label.set_text("")
            # --- End Modern End-Effector Control Card ---

            # --- Modern Gripper Control Expansion ---
            with ui.expansion('Gripper Control', icon='precision_manufacturing', value=False).classes('w-[600px] max-w-full bg-gradient-to-br from-yellow-50 to-orange-100 border border-yellow-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300').props('expand-icon="expand_more"'):
                with ui.row().classes('items-center mb-1'):
                    ui.icon('precision_manufacturing').classes('text-2xl text-yellow-700 mr-2')
                    ui.label('Gripper Control').classes('text-xl font-bold text-yellow-900 tracking-wide')
                ui.separator().classes('my-1')
                ui.label("Control the gripper's movement.").classes('text-gray-600 mb-2')
                with ui.row().classes('justify-center gap-4'):
                    ui.button("Open Gripper", on_click=lambda: utils.open_gripper(Arctos)) \
                        .tooltip("Send command to open the robot gripper") \
                        .classes('bg-yellow-500 text-white px-4 py-2 rounded-lg shadow hover:bg-yellow-600')
                    ui.button("Close Gripper", on_click=lambda: utils.close_gripper(Arctos)) \
                        .tooltip("Send command to close the robot gripper") \
                        .classes('bg-orange-500 text-white px-4 py-2 rounded-lg shadow hover:bg-orange-600')

            # ---------------------- Path‑Planning Section (DROP‑IN) ----------------------
            # Replace the old "Modern Path Planning Expansion" block in *control.py*
            # with everything between the two comment lines below.
            # ---------------------------------------------------------------------------

            # --- Modern Path Planning Expansion ---------------------------------------
            with ui.expansion('Path Planning', icon='map', value=False) \
                    .classes(
                        'w-full bg-gradient-to-br from-green-50 to-blue-100 border border-green-200 '
                        'rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300'):

                # Header ---------------------------------------------------------------
                with ui.row().classes('items-center mb-1'):
                    ui.icon('map').classes('text-2xl text-green-700 mr-2')
                    ui.label('Path Planning').classes('text-xl font-bold text-green-900 tracking-wide')
                ui.separator().classes('my-1')
                ui.label('Manage and execute path‑planning tasks.')\
                    .classes('text-gray-600 mb-2')

                # Tabs -----------------------------------------------------------------
                with ui.tabs().classes('mb-2') as tabs:
                    tab_poses   = ui.tab('Saved Poses',    icon='list_alt')
                    tab_actions = ui.tab('Program Actions', icon='play_circle')

                with ui.tab_panels(tabs, value=tab_poses):

                    # ── SAVED POSES TAB ───────────────────────────────────────────────
                    with ui.tab_panel(tab_poses):

                        ui.button('➕  Add Current Pose',
                                on_click=lambda: (
                                    utils.save_pose(planner, robot),
                                    utils.update_pose_table(planner, robot, pose_container)
                                ))\
                        .classes('w-full mb-2 bg-blue-600 text-white font-semibold py-2 rounded-xl '
                                'shadow hover:bg-blue-800 transition-colors')\
                        .tooltip('Quickly save the current robot pose')

                        # Scroll wrapper keeps the table inside card boundaries --------
                        with ui.element('div')\
                                .classes('w-full max-h-[35vh] overflow-y-auto overflow-x-auto '
                                        'rounded-xl border border-blue-200 bg-white shadow-inner'):
                            pose_container = ui.column().classes('w-full gap-y-2')
                            utils.update_pose_table(planner, robot, pose_container)

                        ui.label('Tip: Click the red × next to a pose to delete it.')\
                        .classes('text-xs text-gray-400 mt-1')

                    # ── PROGRAM ACTIONS TAB ───────────────────────────────────────────
                    with ui.tab_panel(tab_actions):

                        ui.label('Program Actions').classes('text-lg font-semibold text-green-900 mb-2')

                        with ui.row().classes('flex-wrap gap-3 mb-3'):
                            ui.button('Save Pose', icon='add_location_alt',
                                    on_click=lambda: (
                                        utils.save_pose(planner, robot),
                                        utils.update_pose_table(planner, robot, pose_container)
                                    ))\
                            .classes('bg-blue-700 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-900')

                            ui.button('Load Program', icon='folder_open',
                                    on_click=lambda: utils.load_program(planner, pose_container, robot))\
                            .classes('bg-green-700 text-white px-4 py-2 rounded-lg shadow hover:bg-green-900')

                            ui.button('Save Program', icon='save',
                                    on_click=lambda: utils.save_program(planner))\
                            .classes('bg-indigo-700 text-white px-4 py-2 rounded-lg shadow hover:bg-indigo-900')

                            ui.button('Execute Program', icon='play_arrow',
                                    on_click=lambda: utils.execute_path(planner, robot, Arctos, settings_manager))\
                            .classes('bg-red-700 text-white px-4 py-2 rounded-lg shadow hover:bg-red-900')

                        ui.label('Tip: Save your program before executing for best results.')\
                        .classes('text-xs text-gray-400 mt-1')
            # ---------------------------------------------------------------------------
            # ------------------- End of Path‑Planning Section --------------------------


            # --- Modern Home & Sleep Buttons ---
            with ui.row().classes('w-full justify-center gap-4 mb-4'):
                ui.button("🏠 Move to Home Pose", on_click=lambda: homing.move_to_zero_pose(Arctos)) \
                    .tooltip("Send robot to predefined 'home' configuration") \
                    .classes('bg-purple-500 text-white px-4 py-2 rounded-lg shadow hover:bg-purple-700')
                ui.button("💤 Move to Sleep Pose", on_click=lambda: homing.move_to_sleep_pose(Arctos)) \
                    .tooltip("Send robot to safe resting position (sleep pose)") \
                    .classes('bg-gray-500 text-white px-4 py-2 rounded-lg shadow hover:bg-gray-700')

        # RIGHT SECTION: MeshCat & Console
        with ui.column().classes('flex-1 min-w-0 gap-2 items-stretch h-full'):
            # --- Modern 3D Visualization & Keyboard Control Card ---
            with ui.card().classes('w-full h-full flex flex-col bg-gradient-to-br from-gray-50 to-blue-100 border border-gray-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-shadow duration-300'):
                with ui.row().classes('items-center mb-1'):
                    ui.icon('monitor').classes('text-2xl text-blue-700 mr-2')
                    ui.label('3D Visualization').classes('text-xl font-bold text-blue-900 tracking-wide')
                ui.separator().classes('my-1')
                # --- Main Flex Column: MeshCat iframe grows, Keyboard Control stays at bottom ---
                with ui.column().classes('flex-1 w-full h-full'):
                    ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 100%; min-height: 320px; border: none;"></iframe>''')\
                        .classes('w-full h-full rounded-lg border border-blue-200 shadow')
                # --- Keyboard Control Card at bottom ---
                with ui.card().classes('w-full bg-white border border-blue-200 rounded-xl shadow p-3 mt-3'):
                    with ui.row().classes('items-center mb-1'):
                        ui.icon('keyboard').classes('text-xl text-blue-600 mr-2')
                        ui.label('Keyboard Control').classes('text-base font-semibold text-blue-800')
                    with ui.row().classes('w-full justify-center items-start gap-6'):
                        # Keyboard Control Switch
                        with ui.column().classes("items-center"):
                            # Visual indicator for keyboard control
                            keyboard_status_label = ui.label("").classes("text-xs font-semibold mb-1")
                            def update_status_label():
                                if keyboard_ctrl.active:
                                    keyboard_status_label.set_text("[ACTIVE]")
                                    keyboard_status_label.classes("text-green-600 font-bold")
                                else:
                                    keyboard_status_label.set_text("[INACTIVE]")
                                    keyboard_status_label.classes("text-gray-400 font-bold")
                            update_status_label()
                            with ui.row().classes('items-center gap-1'):
                                ui.label("🎮 Keyboard Control").classes("text-sm font-medium text-gray-700 mb-1")
                                with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                                    with ui.tooltip().classes("text-body2 text-left"):
                                        ui.html(
                                            """
                                            <strong>Keyboard Control:</strong><br>
                                            Enable or disable keyboard-based robot movement.<br><br>
                                            <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                                <li><b>W/S</b>: Move along Y-axis</li>
                                                <li><b>A/D</b>: Move along X-axis</li>
                                                <li><b>Q/E</b>: Move along Z-axis</li>
                                            </ul>
                                            Movement is velocity-based while keys are held.<br>
                                            Use the <b>step size</b> slider to adjust increments.<br>
                                            """
                                        )
                            keyboard_control_switch = ui.switch("Keyboard Control", value=keyboard_ctrl.active)
                            def on_switch(val):
                                # Use the controller's toggle logic
                                if val != keyboard_ctrl.active:
                                    keyboard_ctrl.toggle()
                                update_status_label()
                            keyboard_control_switch.on('update:model-value', on_switch)

                        # 🪜 Step Size Slider with Label + Tooltip
                        with ui.column().classes("items-center"):
                            with ui.row().classes("items-center gap-1"):
                                ui.label("Step Size (m)").classes("text-sm font-medium text-gray-700")
                                ui.icon("info").tooltip("Determines how far the robot moves per key press (W/A/S/D/Q/E).")

                            step_size_slider = ui.slider(
                                min=0.0005,
                                max=0.02,
                                value=0.002,
                                step=0.0005
                            ).props('label-always').classes('w-64')
                            # Attach slider to controller
                            keyboard_ctrl.step_size_input = step_size_slider


    # UI timers
    # live update of the joint positions
    ui.timer(0.25, lambda: utils.update_joint_states(robot, joint_positions))
    # live update of the ee position
    ui.timer(0.25, lambda: utils.live_update_ee_postion(robot, ee_position_labels))
    # live update of the ee orientation
    ui.timer(0.25, lambda: utils.live_update_ee_orientation(robot, ee_orientation_labels))
    # Conditional UI Timers, live update of the joint states encoder
    if settings_manager.get("enable_live_joint_updates", True):
        ui.timer(0.3, lambda: utils.threaded_initialize_current_joint_states(robot, Arctos))
        ui.timer(0.25, lambda: utils.update_joint_states_encoder(robot, joint_positions_encoder))