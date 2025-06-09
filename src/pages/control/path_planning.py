from nicegui import ui
import numpy as np
import time
from threading import Thread

def save_pose_action(planner, robot, action_container) -> None:
    """
    Save the current robot pose as a 'POSE' action.
    Args:
        planner: The path planner instance.
        robot: The robot instance.
        action_container: The UI container to update.
    """
    time.sleep(0.5) # Ensure robot state is settled
    planner.capture_pose(robot)
    ui.notify("✅ Pose Action added!")
    update_action_table(planner, robot, action_container)

def add_wait_action_ui(planner, robot, action_container) -> None:
    """
    Opens a dialog to add a 'WAIT' action.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label("Add Wait Action").classes('text-xl font-bold')
        duration_input = ui.number(label="Duration (ms)", value=1000, min=1, step=100).classes('w-full')
        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500')
            def _save_wait():
                planner.add_wait_action(int(duration_input.value), robot)
                ui.notify(f"✅ Wait Action ({duration_input.value}ms) added!")
                update_action_table(planner, robot, action_container)
                dialog.close()
            ui.button("Add Wait", on_click=_save_wait).classes('bg-yellow-600')
    dialog.open()

def add_gripper_action_ui(planner, robot, action_container) -> None:
    """
    Opens a dialog to add a 'GRIPPER' action.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label("Add Gripper Action").classes('text-xl font-bold')
        gripper_command_select = ui.select(options=["OPEN", "CLOSE"], value="OPEN", label="Gripper Command").classes('w-full')
        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500')
            def _save_gripper():
                planner.add_gripper_action(gripper_command_select.value, robot)
                ui.notify(f"✅ Gripper Action ({gripper_command_select.value}) added!")
                update_action_table(planner, robot, action_container)
                dialog.close()
            ui.button("Add Gripper", on_click=_save_gripper).classes('bg-purple-600')
    dialog.open()

def save_program_ui(planner) -> None: # Renamed to avoid conflict, consistent naming
    """
    Save the entire program with an optional name.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label("Save Program").classes('text-xl font-bold')
        program_name_input = ui.input(label="Program Name", placeholder="Enter program name", value=planner.filename).classes('w-full')
        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500')
            def _save_with_name(name):
                if name:
                    success, message = planner.save_program(name)
                    ui.notify(message, color='positive' if success else 'negative')
                else:
                    ui.notify("⚠️ Please enter a program name", color='warning')
                dialog.close()
            ui.button("Save", on_click=lambda: _save_with_name(program_name_input.value)).classes('bg-blue-700')
    dialog.open()

def load_program_ui(planner, action_container, robot) -> None: # Renamed
    """
    Load a saved program.
    """
    available_programs = planner.get_available_programs()
    with ui.dialog() as dialog, ui.card():
        ui.label("Load Program").classes('text-xl font-bold')
        if not available_programs:
            ui.label("No saved programs found.").classes('text-gray-600')
            program_select = None
        else:
            program_select = ui.select(options=available_programs, label="Select Program", value=planner.filename if planner.filename in available_programs else (available_programs[0] if available_programs else None)).classes('w-full')
        
        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500')
            if available_programs and program_select is not None:
                def _load_selected_program(name):
                    if name:
                        success, message = planner.load_program(name, robot)
                        ui.notify(message, color='positive' if success else 'negative')
                        if success:
                            update_action_table(planner, robot, action_container)
                    else:
                        ui.notify("⚠️ Please select a program", color='warning')
                    dialog.close()
                ui.button("Load", on_click=lambda: _load_selected_program(program_select.value)).classes('bg-green-700')
    dialog.open()

def execute_program_ui(planner, robot, arctos, settings_manager) -> None: # Renamed
    """
    Execute the stored program on the robot.
    """
    speed_cfg = settings_manager.get("joint_speeds", {i: 500 for i in range(6)})
    speeds = [speed_cfg.get(str(i), 500) for i in range(6)] # Ensure keys are strings if from JSON
    acceleration_cfg = settings_manager.get("joint_accelerations", {i: 150 for i in range(6)})
    acceleration = [acceleration_cfg.get(str(i), 150) for i in range(6)] # Ensure keys are strings

    # Use the renamed execute_program from PathPlanner
    Thread(target=lambda: planner.execute_program(robot, arctos, speeds=speeds, acceleration=acceleration), daemon=True).start()
    ui.notify("ℹ️ Program executing …", color='info')

def update_action_table(planner, robot, action_container) -> None:
    """
    Update the UI table to display stored actions.
    """
    action_container.clear()
    with action_container:
        with ui.row().classes('w-full items-center justify-between'):
            ui.label("Stored Actions").classes('text-xl font-bold')
            action_count = len(planner.program)
            ui.label(f"{action_count} {'Action' if action_count == 1 else 'Actions'}").classes('text-sm text-gray-500')

        if not planner.program:
            with ui.card().classes('w-full flex items-center justify-center p-8 bg-gray-50 border border-gray-200 rounded-xl'):
                with ui.column().classes('items-center gap-2'):
                    ui.icon('list_alt_add', size='3rem').classes('text-gray-400')
                    ui.label("No actions stored").classes('text-lg text-gray-500')
                    ui.label("Add actions using the buttons below.").classes('text-sm text-gray-400')
            return

        with ui.element('table').classes('w-full rounded-xl overflow-hidden border bg-white shadow-sm'):
            with ui.element('thead').classes('bg-gray-50'):
                with ui.element('tr'):
                    with ui.element('th').classes('px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider').style('width: 5%;'):
                        ui.label('#')
                    with ui.element('th').classes('px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider').style('width: 15%;'):
                        ui.label('Type')
                    with ui.element('th').classes('px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider').style('width: 60%;'):
                        ui.label('Details')
                    with ui.element('th').classes('px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider').style('width: 20%;'):
                        ui.label('Delete')
            with ui.element('tbody'):
                for idx, action_item in enumerate(planner.program):
                    with ui.element('tr').classes('hover:bg-blue-50 transition-colors group'):
                        with ui.element('td').classes('text-center font-medium text-gray-700 p-2'):
                            ui.label(f"{idx+1}").classes('w-8 h-8 flex items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-green-500 text-white group-hover:scale-105 transition-transform')
                        with ui.element('td').classes('p-2'):
                            action_type_str = action_item.get("type", "Unknown")
                            icon_map = {"POSE": "control_camera", "WAIT": "hourglass_empty", "GRIPPER": "front_hand"}
                            with ui.row().classes('items-center gap-2'):
                                ui.icon(icon_map.get(action_type_str, 'help_outline'), color='gray-600')
                                ui.label(action_type_str).classes('font-mono text-sm')
                        with ui.element('td').classes('p-2 font-mono text-xs'):
                            details_str = ""
                            if action_type_str == "POSE":
                                joints_deg = [f"{np.degrees(float(j)):.1f}°" for j in action_item.get("joints", [])]
                                cart_coords = [f"{float(c):.3f}" for c in action_item.get("cartesian", [])]
                                details_str = f"Joints: {', '.join(joints_deg)}\nCartesian: ({', '.join(cart_coords)})"
                            elif action_type_str == "WAIT":
                                duration = action_item.get("duration_ms", 0)
                                details_str = f"Duration: {duration} ms"
                            elif action_type_str == "GRIPPER":
                                command = action_item.get("command", "N/A")
                                details_str = f"Command: {command}"
                            else:
                                details_str = str(action_item)
                            ui.label(details_str).style('white-space: pre-wrap;') # Allow multi-line details
                        with ui.element('td').classes('text-center p-2'):
                            ui.button(icon='delete', color='red', on_click=lambda i=idx: delete_action_ui(planner, i, robot, action_container)).props('flat round dense').tooltip(f"Delete Action {idx+1}")

def delete_action_ui(planner, index, robot, action_container) -> None:
    """
    Delete a stored action, update UI table, and visualization.
    """
    planner.delete_action(index, robot) # PathPlanner's delete_action handles visualization
    update_action_table(planner, robot, action_container)
    ui.notify(f"🗑️ Action {index + 1} deleted.", color='warning')

def path_planning(planner, robot, Arctos, settings_manager) -> None:
    """
    Create the path planning UI expansion.
    """
    expansion_common = (
        "w-full bg-white/90 backdrop-blur-md border border-blue-200 "
        "rounded-md shadow-xl p-0 transition-all duration-300 "
        "hover:shadow-2xl"
    )
    with ui.expansion('Path Planning', icon='route', value=False).classes(expansion_common).props('expand-icon="expand_more"'):
        action_container = ui.column().classes('w-full gap-y-4 p-4') # Added padding to container
        update_action_table(planner, robot, action_container)

        ui.element('hr').classes('my-4 border-gray-200')

        with ui.grid().classes('w-full grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 p-4'): # Adjusted grid for more buttons
            # Card style
            card_classes = 'bg-white p-4 rounded-xl border hover:shadow-lg transition-all flex flex-col items-center justify-center text-center gap-2'
            button_classes = 'w-full text-white px-4 py-2 rounded-lg text-sm font-medium'

            # Save Pose Action Button
            with ui.card().classes(f'{card_classes} border-blue-100 hover:bg-blue-50'):
                ui.icon('add_location_alt', size='2rem').classes('text-blue-600')
                ui.label('Add Pose').classes('font-semibold text-blue-800')
                ui.button('+', on_click=lambda: save_pose_action(planner, robot, action_container)).classes(f'{button_classes} bg-blue-600 hover:bg-blue-700')

            # Add Wait Action Button
            with ui.card().classes(f'{card_classes} border-yellow-100 hover:bg-yellow-50'):
                ui.icon('hourglass_empty', size='2rem').classes('text-yellow-600')
                ui.label('Add Wait').classes('font-semibold text-yellow-800')
                ui.button('+', on_click=lambda: add_wait_action_ui(planner, robot, action_container)).classes(f'{button_classes} bg-yellow-500 hover:bg-yellow-600')

            # Add Gripper Action Button
            with ui.card().classes(f'{card_classes} border-purple-100 hover:bg-purple-50'):
                ui.icon('front_hand', size='2rem').classes('text-purple-600')
                ui.label('Add Gripper').classes('font-semibold text-purple-800')
                ui.button('+', on_click=lambda: add_gripper_action_ui(planner, robot, action_container)).classes(f'{button_classes} bg-purple-500 hover:bg-purple-600')

            # Load Program Button
            with ui.card().classes(f'{card_classes} border-green-100 hover:bg-green-50'):
                ui.icon('folder_open', size='2rem').classes('text-green-600')
                ui.label('Load Program').classes('font-semibold text-green-800')
                ui.button('Load', on_click=lambda: load_program_ui(planner, action_container, robot)).classes(f'{button_classes} bg-green-600 hover:bg-green-700')

            # Save Program Button
            with ui.card().classes(f'{card_classes} border-indigo-100 hover:bg-indigo-50'):
                ui.icon('save', size='2rem').classes('text-indigo-600')
                ui.label('Save Program').classes('font-semibold text-indigo-800')
                ui.button('Save', on_click=lambda: save_program_ui(planner)).classes(f'{button_classes} bg-indigo-600 hover:bg-indigo-700')

            # Execute Program Button
            with ui.card().classes(f'{card_classes} border-red-100 hover:bg-red-50 col-span-1 sm:col-span-2 lg:col-span-3 xl:col-span-5'): # Make execute button wider
                ui.icon('play_circle_filled', size='2rem').classes('text-red-600')
                ui.label('Run Program').classes('font-semibold text-red-800')
                ui.button('Execute Program', on_click=lambda: execute_program_ui(planner, robot, Arctos, settings_manager)).classes(f'{button_classes} bg-red-600 hover:bg-red-700')

        with ui.row().classes('bg-blue-50 p-3 rounded-xl border border-blue-100 items-center gap-2 mt-4 mx-4 mb-4'): # Added margin
            ui.icon('info').classes('text-blue-500')
            ui.label('Programs are sequences of actions. Save your program before executing for best results.').classes('text-sm text-blue-700')
