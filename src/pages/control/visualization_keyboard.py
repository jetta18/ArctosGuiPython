"""
Module for creating the 3D visualization keyboard UI section.

This module provides a function to build the UI for controlling the 3D robot visualization using NiceGUI components.
"""

from nicegui import ui

def visualization_keyboard(robot, Arctos, keyboard_ctrl, step_size_slider, update_status_label, on_switch):
    """
    Create the visualization keyboard UI section for controlling the 3D robot visualization.

    Args:
        robot: The robot object associated with the visualization.
        Arctos: The Arctos object associated with the visualization.
        keyboard_ctrl: The keyboard control object for the visualization.
        step_size_slider: The step size slider object for the visualization.
        update_status_label: A function to update the status label.
        on_switch: A function to call when the keyboard control switch is toggled.

    Returns:
        None. The function builds the UI directly using NiceGUI components.

    Raises:
        None.
    """
    with ui.card().classes('w-full h-full flex flex-col bg-gradient-to-br from-gray-50 to-blue-100 border border-gray-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-shadow duration-300'):
        with ui.row().classes('items-center mb-1'):
            ui.icon('monitor').classes('text-2xl text-blue-700 mr-2')
            ui.label('3D Visualization').classes('text-xl font-bold text-blue-900 tracking-wide')
        with ui.column().classes('flex-1 w-full h-full'):
            ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 100%; min-height: 320px; border: none;"></iframe>''')\
                .classes('w-full h-full rounded-lg border border-blue-200 shadow')
        with ui.card().classes('w-full bg-white border border-blue-200 rounded-xl shadow p-3 mt-3'):
            with ui.row().classes('items-center mb-1'):
                ui.icon('keyboard').classes('text-xl text-blue-600 mr-2')
                ui.label('Keyboard Control').classes('text-base font-semibold text-blue-800')
            with ui.row().classes('w-full justify-center items-start gap-6'):
                with ui.column().classes("items-center"):
                    # Removed keyboard_status_label and update_status_label logic
                    with ui.row().classes('items-center gap-2'):
                        keyboard_control_switch = ui.switch("Keyboard Control", value=keyboard_ctrl.active)
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
                        def on_switch(val):
                            # Use the controller's toggle logic
                            if val != keyboard_ctrl.active:
                                keyboard_ctrl.toggle()
                            # No status label update needed
                        keyboard_control_switch.on('update:model-value', on_switch)
                with ui.column().classes("items-center"):
                    with ui.row().classes("items-center gap-2"):
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
                    ).props('label-always').classes('w-64')
                    # Attach slider to controller
                    keyboard_ctrl.step_size_input = step_size_slider
