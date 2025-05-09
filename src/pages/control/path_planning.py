from nicegui import ui
import numpy as np
import time
from threading import Thread

def save_pose(planner, robot) -> None:
    """
    Save the current robot pose.

    Captures the robot's current joint states and Cartesian coordinates, then stores the pose using the provided planner instance.

    Args:
        planner: The path planner instance responsible for managing and storing robot poses.
        robot: The robot instance, which provides methods to retrieve current joint states and Cartesian coordinates.

    Returns:
        None
    """
    time.sleep(0.5)
    planner.capture_pose(robot)
    ui.notify("✅ Pose saved successfully!")

def save_program(planner, program_name=None) -> None:
    """
    Save the entire sequence of poses stored in the planner with an optional name.

    If a program name is not provided, prompts the user to input a name via a dialog. The program is then saved with the given name.

    Args:
        planner: The path planner instance containing the sequence of stored poses.
        program_name (str, optional): Optional name for the program file. If not provided, a dialog will prompt the user. Defaults to None.

    Returns:
        None
    """
    if program_name is None:
        # Create a dialog to get the program name
        with ui.dialog() as dialog, ui.card():
            ui.label("Save Program").classes('text-xl font-bold')
            program_name_input = ui.input(label="Program Name", placeholder="Enter program name").classes('w-full')

            with ui.row().classes('w-full justify-end'):
                ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')
                ui.button("Save", on_click=lambda: save_with_name(program_name_input.value)).classes('bg-blue-700 text-white px-4 py-2 rounded-lg')

            def save_with_name(name):
                if name:
                    success, message = planner.save_program(name)
                    ui.notify(message, color='green' if success else 'red')
                else:
                    ui.notify("⚠️ Please enter a program name", color='orange')
                dialog.close()

        dialog.open()
    else:
        success, message = planner.save_program(program_name)
        ui.notify(message, color='green' if success else 'red')


def load_program(planner, pose_container=None, robot=None) -> None:
    """
    Load a saved program of robot poses.

    Presents a dialog to the user to select and load a previously saved program of robot poses. Upon successful loading, optionally updates the UI container and robot visualization.

    Args:
        planner: The path planner instance managing the pose sequence and loading.
        pose_container (ui.element, optional): UI container to update with loaded poses. Defaults to None.
        robot: Optional robot instance for updating the robot's pose visualization. Defaults to None.

    Returns:
        None
    """
    # Get available programs
    available_programs = planner.get_available_programs()

    # Create a dialog to select the program
    with ui.dialog() as dialog, ui.card():
        ui.label("Load Program").classes('text-xl font-bold')

        if not available_programs:
            ui.label("No saved programs found").classes('text-gray-600')
        else:
            program_select = ui.select(
                options=available_programs,
                label="Select Program",
                value=available_programs[0] if available_programs else None
            ).classes('w-full')

        with ui.row().classes('w-full justify-end'):
            ui.button("Cancel", on_click=dialog.close).classes('bg-gray-500 text-white px-4 py-2 rounded-lg')

            if available_programs:
                ui.button("Load", on_click=lambda: load_selected_program(program_select.value)).classes('bg-green-700 text-white px-4 py-2 rounded-lg')

        def load_selected_program(program_name):
            if program_name:
                success, message = planner.load_program(program_name, robot)
                ui.notify(message, color='green' if success else 'red')

                # Update pose table if container and robot are provided
                if success and pose_container is not None and robot is not None:
                    update_pose_table(planner, robot, pose_container)
            else:
                ui.notify("Please select a program", color='orange')
                
            dialog.close()

    dialog.open()


def execute_path(planner, robot, arctos, settings_manager) -> None:
    """
    Execute a stored path (program) on the robot.

    Iterates through the stored poses in the planner and commands the robot to execute them in sequence.
    Handles speed scaling and other settings as configured.

    Args:
        planner: The path planner instance containing the sequence of poses.
        robot: The robot instance to be controlled.
        arctos: The robot controller interface.
        settings_manager: The settings manager instance for runtime settings.

    Returns:
        None

    Raises:
        Exception: For any errors during path execution or robot communication.
    """
    speed_cfg = settings_manager.get("joint_speeds", {i: 500 for i in range(6)})
    speeds = [speed_cfg.get(i, 500) for i in range(6)]

    Thread(target=lambda: planner.execute_path(robot, arctos, speeds=speeds), daemon=True).start()
    ui.notify("Path executing …")


def update_pose_table(planner, robot, pose_container) -> None:
    """
    Update the UI table to display stored poses, including joint angles and Cartesian coordinates.

    Args:
        planner: The path planner instance managing stored poses.
        robot: The robot instance required for pose deletion.
        pose_container: The UI container where the pose table will be rendered.

    Returns:
        None

    Raises:
        Exception: For any errors during table updates or pose rendering.
    """
    # Clear the container
    pose_container.clear()

    with pose_container:
        with ui.row().classes('w-full items-center justify-between'):
            ui.label("Stored Poses").classes('text-xl font-bold')
            pose_count = len(planner.poses)
            ui.label(f"{pose_count} {'Pose' if pose_count == 1 else 'Poses'}").classes('text-sm text-gray-500')

        if not planner.poses:
            with ui.card().classes('w-full flex items-center justify-center p-8 bg-gray-50 border border-gray-200 rounded-xl'):
                with ui.column().classes('items-center gap-2'):
                    ui.icon('gesture', size='3rem').classes('text-gray-400')
                    ui.label("No poses stored").classes('text-lg text-gray-500')
                    ui.label("Create a pose by clicking 'Save Pose'").classes('text-sm text-gray-400')
            return

        # Single, modern, minimalistic table for all pose data
        with ui.element('table').classes('w-full rounded-xl overflow-hidden border bg-white shadow-sm'):
            with ui.element('thead').classes('bg-blue-50'):
                with ui.element('tr'):
                    with ui.element('th').classes('py-2 text-center w-8'):
                        ui.label('#').classes('font-semibold')
                    with ui.element('th').classes('py-2 text-center'):
                        ui.label('Joint Angles (°)').classes('font-semibold')
                    with ui.element('th').classes('py-2 text-center'):
                        ui.label('Cartesian (X, Y, Z) [m]').classes('font-semibold')
                    with ui.element('th').classes('py-2 text-center w-16'):
                        ui.label('Delete').classes('font-semibold')
            with ui.element('tbody'):
                for idx, pose in enumerate(planner.poses):
                    try:
                        joints = [f"{np.degrees(float(j)):.1f}°" for j in pose["joints"]]
                        cartesian = [f"{float(c):.3f}" for c in pose["cartesian"]]
                        with ui.element('tr').classes('hover:bg-blue-50 transition-colors group'):
                            with ui.element('td').classes('text-center font-medium text-gray-700'):
                                ui.label(f"{idx+1}").classes('w-8 h-8 flex items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-green-500 text-white group-hover:scale-105 transition-transform')
                            with ui.element('td').classes('text-center font-mono text-sm text-blue-900'):
                                ui.label(f'{", ".join(joints)}')
                            with ui.element('td').classes('text-center font-mono text-sm text-green-900'):
                                ui.label(f'({cartesian[0]}, {cartesian[1]}, {cartesian[2]})')
                            with ui.element('td').classes('text-center'):
                                ui.button(icon='delete', color='red', on_click=lambda i=idx: delete_pose(planner, i, robot, pose_container)).props('flat round').classes('text-red-500 hover:bg-red-50').tooltip(f"Delete Pose {idx+1}")
                    except Exception as e:
                        print(f"Error displaying pose {idx}: {e}")


def delete_pose(planner, index, robot, pose_container) -> None:
    """
    Delete a stored pose, update the UI table, and remove the corresponding MeshCat visualization.

    Args:
        planner: The path planner instance managing stored poses.
        index (int): The index of the pose to delete.
        robot: The robot instance required to remove the visualization from MeshCat.
        pose_container: The UI container for updating the pose table.

    Returns:
        None

    Raises:
        Exception: For any errors during pose deletion or UI updates.
    """
    planner.delete_pose(index, robot)
    update_pose_table(planner, robot, pose_container)


def path_planning(planner, robot, Arctos, settings_manager) -> None:
    """
    Create the path planning expansion for the robot.

    Args:
        planner: The path planning module or object.
        robot: The robot instance for which paths are being planned.
        Arctos: The main robot control interface or object.
        settings_manager: The settings manager for user preferences and state.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    with ui.expansion('Path Planning', icon='route', value=False).classes('w-full bg-gradient-to-br from-green-50 to-blue-100 border border-green-200 rounded-2xl shadow-lg p-4 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        # Pose Table
        pose_container = ui.column().classes('w-full gap-y-4')
        update_pose_table(planner, robot, pose_container)

        # Visual Divider
        ui.element('hr').classes('my-4 border-gray-200')

        # Action Buttons Grid
        with ui.grid().classes('w-full grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3'):
            # Save Pose Button
            with ui.card().classes('bg-white p-3 rounded-xl border border-blue-100 hover:bg-blue-50 transition-all'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('add_location_alt').classes('text-blue-600 text-2xl')
                    ui.label('Save Pose').classes('font-medium text-blue-800')
                ui.button('Save', icon='save', on_click=lambda: (
                    save_pose(planner, robot),
                    update_pose_table(planner, robot, pose_container)
                )).classes('bg-blue-600 text-white px-4 py-1 rounded-lg text-sm')

            # Load Program Button
            with ui.card().classes('bg-white p-3 rounded-xl border border-green-100 hover:bg-green-50 transition-all'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('folder_open').classes('text-green-600 text-2xl')
                    ui.label('Load Program').classes('font-medium text-green-800')
                ui.button('Load', icon='download', on_click=lambda: load_program(planner, pose_container, robot)).classes('bg-green-600 text-white px-4 py-1 rounded-lg text-sm')

            # Save Program Button
            with ui.card().classes('bg-white p-3 rounded-xl border border-indigo-100 hover:bg-indigo-50 transition-all'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('save').classes('text-indigo-600 text-2xl')
                    ui.label('Save Program').classes('font-medium text-indigo-800')
                ui.button('Save', icon='upload', on_click=lambda: save_program(planner)).classes('bg-indigo-600 text-white px-4 py-1 rounded-lg text-sm')

            # Execute Program Button
            with ui.card().classes('bg-white p-3 rounded-xl border border-red-100 hover:bg-red-50 transition-all'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('play_arrow').classes('text-red-600 text-2xl')
                    ui.label('Run Program').classes('font-medium text-red-800')
                ui.button('Run', icon='smart_toy', on_click=lambda: execute_path(planner, robot, Arctos, settings_manager)).classes('bg-red-600 text-white px-4 py-1 rounded-lg text-sm')

        # Info note
        with ui.row().classes('bg-blue-50 p-3 rounded-xl border border-blue-100 items-center gap-2 mt-2'):
            ui.icon('info').classes('text-blue-500')
            ui.label('Save your program before executing for best results').classes('text-sm text-blue-700')
