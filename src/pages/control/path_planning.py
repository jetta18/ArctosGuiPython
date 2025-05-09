from nicegui import ui
import numpy as np
import time

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
        ui.label("Stored Poses").classes('text-xl font-bold mb-2')

        if not planner.poses:
            ui.label("No stored poses!").classes('text-red-500')
            return

        # Create a table for stored poses (excluding buttons)
        pose_table = ui.table(columns=[
            {"name": "pose", "label": "Pose #", "field": "pose"},
            {"name": "j1", "label": "J1 (°)", "field": "j1"},
            {"name": "j2", "label": "J2 (°)", "field": "j2"},
            {"name": "j3", "label": "J3 (°)", "field": "j3"},
            {"name": "j4", "label": "J4 (°)", "field": "j4"},
            {"name": "j5", "label": "J5 (°)", "field": "j5"},
            {"name": "j6", "label": "J6 (°)", "field": "j6"},
            {"name": "x", "label": "X (m)", "field": "x"},
            {"name": "y", "label": "Y (m)", "field": "y"},
            {"name": "z", "label": "Z (m)", "field": "z"},
        ], rows=[]).classes("w-full border")

        button_container = ui.row()  # Store delete buttons separately

        for idx, pose in enumerate(planner.poses):
            try:
                joints = [f"{np.degrees(float(j)):.2f}°" for j in pose["joints"]]
                cartesian = [f"{float(c):.3f}" for c in pose["cartesian"]]

                row = {
                    "pose": idx + 1,
                    "j1": joints[0], "j2": joints[1], "j3": joints[2],
                    "j4": joints[3], "j5": joints[4], "j6": joints[5],
                    "x": cartesian[0], "y": cartesian[1], "z": cartesian[2]
                }

                pose_table.rows.append(row)

                with button_container:
                    ui.button(f"Delete Pose {idx + 1}", on_click=lambda i=idx: delete_pose(planner, i, robot, pose_container)).classes('bg-red-500 text-white px-3 py-1 rounded-lg mt-1')

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
    planner.delete_pose(index, robot)  # Call delete function in PathPlanner
    update_pose_table(planner, robot, pose_container)


def path_planning(planner, robot, Arctos, settings_manager):
    """Create the path planning expansion for the robot.

    Args:
        planner: The path planning module or object.
        robot: The robot instance for which paths are being planned.
        Arctos: The main robot control interface or object.
        settings_manager: The settings manager for user preferences and state.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    with ui.expansion('Path Planning', icon='map', value=False).classes('w-full bg-gradient-to-br from-green-50 to-blue-100 border border-green-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        ui.label('Manage and execute path‑planning tasks.')\
            .classes('text-gray-600 mb-2')
        with ui.tabs().classes('mb-2') as tabs:
            tab_poses   = ui.tab('Saved Poses',    icon='list_alt')
            tab_actions = ui.tab('Program Actions', icon='play_circle')
        with ui.tab_panels(tabs, value=tab_poses):
            with ui.tab_panel(tab_poses):
                pose_container = ui.column().classes('w-full gap-y-2')
                update_pose_table(planner, robot, pose_container)
                ui.label('Tip: Click the red × next to a pose to delete it.')\
                    .classes('text-xs text-gray-400 mt-1')
            with ui.tab_panel(tab_actions):
                ui.label('Program Actions').classes('text-lg font-semibold text-green-900 mb-2')
                with ui.row().classes('flex-wrap gap-3 mb-3'):
                    ui.button('Save Pose', icon='add_location_alt',
                        on_click=lambda: (
                            save_pose(planner, robot),
                            update_pose_table(planner, robot, pose_container)
                        ))\
                        .classes('bg-blue-700 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-900')
                    ui.button('Load Program', icon='folder_open',
                        on_click=lambda: load_program(planner, pose_container, robot))\
                        .classes('bg-green-700 text-white px-4 py-2 rounded-lg shadow hover:bg-green-900')
                    ui.button('Save Program', icon='save',
                        on_click=lambda: save_program(planner))\
                        .classes('bg-indigo-700 text-white px-4 py-2 rounded-lg shadow hover:bg-indigo-900')
                    ui.button('Execute Program', icon='play_arrow',
                        on_click=lambda: execute_path(planner, robot, Arctos, settings_manager))\
                        .classes('bg-red-700 text-white px-4 py-2 rounded-lg shadow hover:bg-red-900')
                ui.label('Tip: Save your program before executing for best results.')\
                    .classes('text-xs text-gray-400 mt-1')
