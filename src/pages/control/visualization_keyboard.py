"""
Module for creating the 3D visualization keyboard UI section.

This module provides a function to build the UI for controlling the 3D robot visualization using NiceGUI components.
"""

from socket import timeout
from nicegui import ui
from nicegui.events import KeyEventArguments
import numpy as np


def visualization_keyboard(robot, Arctos, step_size_slider=None, update_status_label=None, on_switch=None, settings_manager=None):
    """
    Create the visualization keyboard UI section for controlling the 3D robot visualization.

    This function sets up a UI section that allows users to control the 3D visualization of a robot using keyboard inputs.
    It provides controls for enabling keyboard-based manipulation of the robot's position and orientation in the 3D scene,
    with adjustable step sizes for both translational and rotational movements. The function also integrates with robot
    hardware to apply calculated inverse kinematics (IK) solutions, optionally sending commands to the robot's hardware
    if enabled in the settings.

    Args:
        robot: The robot instance used for retrieving and setting end-effector positions and orientations.
        Arctos: The main robot control interface or object responsible for executing movement commands.
        step_size_slider: Optional UI slider component for controlling the step size of position movements.
        update_status_label: Optional function to update UI status labels based on the robot's state.
        on_switch: Optional callback function triggered when the keyboard control switch is toggled.
        settings_manager: Optional settings manager for accessing user preferences, particularly related to sending commands
                          to the robot hardware.

    Returns:
        None. The function constructs and displays the UI components directly using NiceGUI.

    Raises:
        None explicitly. However, it may raise exceptions if the robot's IK solution fails or hardware commands cannot be sent.
    """
    # --- State for keyboard control ---
    keyboard_control_enabled = {'value': False}  # Mutable state for closure

    # Define key_map once for both handlers
    key_map = {
        'a': ('x', -1), 'd': ('x', 1),
        'w': ('y', -1), 's': ('y', 1),
        'q': ('z', 1),  'e': ('z', -1),
        'j': ('roll', -1), 'l': ('roll', 1),
        'i': ('pitch', -1), 'k': ('pitch', 1),
        'u': ('yaw', -1), 'o': ('yaw', 1),
    }

    pressed_keys = set()
    def handle_key(e: KeyEventArguments):
        if not keyboard_control_enabled['value']:
            return
        key = e.key.name
        if key not in key_map:
            return
        if e.action.keydown:
            pressed_keys.add(key)
        elif e.action.keyup:
            pressed_keys.discard(key)

    def process_pressed_keys():
        if not keyboard_control_enabled['value']:
            return
        if not pressed_keys:
            return
        step = step_size_slider.value if step_size_slider else 0.002
        orientation_step = np.radians(5)
        try:
            orientation_step = np.radians(orientation_step_size_slider.value)
        except Exception:
            pass
        current_pos = robot.get_end_effector_position()
        current_rpy = robot.get_end_effector_orientation()
        for key in pressed_keys:
            axis, sign = key_map[key]
            if axis in ['x', 'y', 'z']:
                idx = {'x': 0, 'y': 1, 'z': 2}[axis]
                current_pos[idx] += sign * step
            else:
                idx = {'roll': 0, 'pitch': 1, 'yaw': 2}[axis]
                current_rpy[idx] += sign * orientation_step
        try:
            q_solution = robot.inverse_kinematics_pink(current_pos, current_rpy)
            robot.instant_display_state(q_solution)
            if settings_manager and settings_manager.get("keyboard_send_to_robot", False):
                speeds = settings_manager.get("joint_speeds", [500]*6)
                accels = settings_manager.get("joint_accelerations", [150]*6)
                if not isinstance(speeds, (list, tuple)):
                    speeds = [speeds]*6
                if not isinstance(accels, (list, tuple)):
                    accels = [accels]*6
                try:
                    Arctos.move_to_angles(q_solution[:6], speeds=speeds, acceleration=accels, wait_for_completion=False)
                except Exception as hw_ex:
                    ui.notify(f"Send to robot failed: {hw_ex}", color="red")
        except Exception as ex:
            ui.notify(f"IK failed: {ex}", color="red")

    # Add NiceGUI keyboard event tracking
    keyboard = ui.keyboard(on_key=handle_key)
    ui.timer(0.1, process_pressed_keys)

    with ui.card().classes('w-full h-full flex flex-col bg-gradient-to-br from-gray-50 to-blue-100 border border-gray-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center mb-1'):
            ui.icon('monitor').classes('text-2xl text-blue-700 mr-2')
            ui.label('3D Visualization').classes('text-xl font-bold text-blue-900 tracking-wide')
        with ui.column().classes('flex-1 w-full h-full'):
            ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 100%; min-height: 320px; border: none;"></iframe>''')\
                .classes('w-full h-full rounded-lg border border-blue-200 shadow')
        with ui.card().classes('w-full bg-white border border-blue-200 rounded-xl shadow p-3 mt-3'):
            # --- Switch and Sliders Aligned in a Single Row ---
            with ui.row().classes('w-full items-center justify-center gap-8 flex-wrap'):
                # Switch + Info
                with ui.column().classes('items-center min-w-[220px]'):
                    with ui.row().classes('items-center gap-2 mb-1'):
                        keyboard_control_switch = ui.switch(
                            "Keyboard Control",
                            value=keyboard_control_enabled['value'],
                            on_change=lambda e: handle_keyboard_switch(e.value)
                        )
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
                                        <li><b>J/L</b>: Roll -/+</li>
                                        <li><b>I/K</b>: Pitch -/+</li>
                                        <li><b>U/O</b>: Yaw -/+</li>
                                    </ul>
                                    Each key press moves the robot stepwise.<br>
                                    Use the <b>step size</b> slider to adjust increments.<br>
                                    """
                                )
                # Step Size (Position) Slider + Info
                with ui.column().classes('items-center min-w-[220px]'):
                    with ui.row().classes("items-center gap-1 mb-1"):
                        ui.label("Step Size (m)").classes("text-sm font-medium text-gray-700")
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Step Size:</strong><br>
                                    Determines how far the robot moves per key press (<b>W/A/S/D/Q/E</b>).<br><br>
                                    <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                        <li>Smaller value: finer, more precise motion</li>
                                        <li>Larger value: faster, coarser steps</li>
                                    </ul>
                                    Adjust as needed for your task.
                                    """
                                )
                    step_size_slider = ui.slider(
                        min=0.0005,
                        max=0.02,
                        value=0.002,
                        step=0.0005
                    ).props('label-always').classes('w-56')
                # Orientation Step Size Slider + Info
                with ui.column().classes('items-center min-w-[220px]'):
                    with ui.row().classes("items-center gap-1 mb-1"):
                        ui.label("Orientation Step (deg)").classes("text-sm font-medium text-gray-700")
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Orientation Step Size:</strong><br>
                                    Determines how much the robot rotates per key press (<b>J/L, I/K, U/O</b>).<br><br>
                                    <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                        <li>Smaller value: finer angle changes</li>
                                        <li>Larger value: faster, coarser angle steps</li>
                                    </ul>
                                    Adjust as needed for your task.
                                    """
                                )
                    orientation_step_size_slider = ui.slider(
                        min=1,
                        max=30,
                        value=5,
                        step=1
                    ).props('label-always').classes('w-56')

            def handle_keyboard_switch(val: bool):
                keyboard_control_enabled['value'] = val
                if val:
                    ui.notify('Keyboard control activated', type='positive', close_button=True, timeout=1500)
                else:
                    ui.notify('Keyboard control deactivated', type='negative', close_button=True, timeout=1500)
                if on_switch:
                    on_switch(val)

