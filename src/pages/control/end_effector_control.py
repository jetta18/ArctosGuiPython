from nicegui import ui

from nicegui import ui
from utils import utils


def end_effector_control(robot):
    """
    Create the end-effector control expansion for the robot, including live display and input fields.

    Args:
        robot: The robot instance whose end-effector is being controlled.

    Returns:
        tuple: Tuple of (position_labels, orientation_labels) as NiceGUI label objects.
    """
    # --- Modern End-Effector Control Expansion ---
    with ui.expansion('End-Effector Control', icon='open_with', value=False).classes('w-full bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
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
        with ui.row().classes('justify-center'):
            mode = ui.toggle(["Position Only", "Position + Orientation", "Orientation Only"], value="Position + Orientation") \
                .classes('max-w-fit')
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
        input_container.move()
        # --- Action Buttons ---
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
    return ee_position_labels, ee_orientation_labels
